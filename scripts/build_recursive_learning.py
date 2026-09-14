#!/usr/bin/env python3
"""Build Q25 recursive-learning dogfood telemetry from committed evidence.

This packet is deliberately diagnostic, not an optimization target.

It asks whether the *research process* is learning across recent campaigns:
- Are destructive controls actually resolving hypotheses?
- Are economically viable, control-supported mechanisms becoming more common?
- Does research-fold excitement survive development?
- Does development survive frozen forward validation?
- Is the public evidence surface keeping up with measurement?
- Is the next action measurement, evidence deepening, calibration, or a new object?

No weighted mega-score is produced. Cross-campaign scalar ranking remains forbidden.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence"
HEALTH = ROOT / "docs" / "data" / "methodology_health.json"
OUT_JSON = ROOT / "docs" / "data" / "recursive_learning.json"
OUT_MD = ROOT / "docs" / "RECURSIVE_LEARNING.md"

ROBUST_FLOOR = 1.0
RECENT_WINDOW = 3


def _load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text())


def _float(value: Any) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def _rate(count: int, total: int) -> float | None:
    return None if total == 0 else count / total


def _median(values: list[float]) -> float | None:
    return None if not values else statistics.median(values)


def _recent_development_summaries(limit: int = RECENT_WINDOW) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(EVIDENCE.glob("frontier_*/observed_summary.json")):
        payload = _load_json(path, {})
        families = payload.get("families")
        stage = str(payload.get("evidence_stage") or payload.get("status") or "")
        if not isinstance(families, list) or not families:
            continue
        if "DEVELOPMENT" not in stage.upper():
            continue
        payload = dict(payload)
        payload["_source_path"] = str(path.relative_to(ROOT))
        rows.append(payload)
    return rows[-limit:]


def _family_metrics(family: dict[str, Any]) -> dict[str, Any]:
    best = _float(family.get("best_robust_sharpe"))
    central = _float(family.get("central_robust_sharpe"))
    ablation = _float(family.get("ablation_robust_sharpe"))
    falsifier = _float(family.get("falsifier_robust_sharpe"))
    controls = [x for x in (ablation, falsifier) if x is not None]
    complete = central is not None and ablation is not None and falsifier is not None
    margin = None if central is None or not controls else central - max(controls)
    supported = margin > 0 if complete and margin is not None else None
    economic = best is not None and best >= ROBUST_FLOOR
    return {
        "family": family.get("family"),
        "best_robust_sharpe": best,
        "central_control_margin": margin,
        "falsification_complete": complete,
        "control_supported": supported,
        "economic_survivor": economic,
        "promotion_ready": bool(economic and supported is True),
        "decision_code": family.get("decision_code"),
    }


def _campaign_row(summary: dict[str, Any]) -> dict[str, Any]:
    family_rows = [_family_metrics(row) for row in summary.get("families", [])]
    total = len(family_rows)
    margins = [
        row["central_control_margin"]
        for row in family_rows
        if row["central_control_margin"] is not None
    ]
    best_values = [
        row["best_robust_sharpe"]
        for row in family_rows
        if row["best_robust_sharpe"] is not None
    ]

    cell_gaps: list[float] = []
    for cell in (summary.get("notable_base_cells") or {}).values():
        research = _float(cell.get("research_sharpe_12"))
        dev = _float(cell.get("dev_sharpe_12"))
        if research is not None and dev is not None:
            cell_gaps.append(dev - research)

    family_names = [
        str(row["family"])
        for row in family_rows
        if row.get("family")
    ]

    falsification_count = sum(row["falsification_complete"] for row in family_rows)
    support_count = sum(row["control_supported"] is True for row in family_rows)
    economic_count = sum(row["economic_survivor"] for row in family_rows)
    promotion_count = sum(row["promotion_ready"] for row in family_rows)
    resolved_count = sum(bool(row.get("decision_code")) for row in family_rows)
    falsified_count = sum(
        str(row.get("decision_code") or "").startswith("FALSIFIED")
        for row in family_rows
    )
    supported_weak_count = sum(
        row["control_supported"] is True and not row["economic_survivor"]
        for row in family_rows
    )

    best = max(best_values) if best_values else None
    nonnegative_gap_count = sum(gap >= 0 for gap in cell_gaps)

    return {
        "campaign": summary.get("campaign"),
        "decision": summary.get("decision"),
        "evidence_stage": summary.get("evidence_stage"),
        "source_path": summary.get("_source_path"),
        "family_count": total,
        "family_names": family_names,
        "falsification_coverage": {
            "count": falsification_count,
            "total": total,
            "rate": _rate(falsification_count, total),
        },
        "control_support": {
            "count": support_count,
            "total": total,
            "rate": _rate(support_count, total),
        },
        "economic_survival": {
            "count": economic_count,
            "total": total,
            "rate": _rate(economic_count, total),
        },
        "promotion_ready": {
            "count": promotion_count,
            "total": total,
            "rate": _rate(promotion_count, total),
        },
        "decision_resolution": {
            "count": resolved_count,
            "total": total,
            "rate": _rate(resolved_count, total),
        },
        "falsified_by_controls_count": falsified_count,
        "control_supported_but_weak_count": supported_weak_count,
        "best_robust_sharpe": best,
        "best_floor_margin": None if best is None else best - ROBUST_FLOOR,
        "median_central_control_margin": _median(margins),
        "research_to_dev": {
            "base_cells_compared": len(cell_gaps),
            "median_dev_minus_research_sharpe_12": _median(cell_gaps),
            "nonnegative_gap_count": nonnegative_gap_count,
            "nonnegative_gap_rate": _rate(nonnegative_gap_count, len(cell_gaps)),
        },
    }


def _direction(values: list[float | None]) -> str:
    clean = [v for v in values if v is not None]
    if len(clean) < 2:
        return "INSUFFICIENT_HISTORY"
    if all(b < a for a, b in zip(clean, clean[1:])):
        return "DOWN"
    if all(b > a for a, b in zip(clean, clean[1:])):
        return "UP"
    if all(b == a for a, b in zip(clean, clean[1:])):
        return "FLAT"
    return "MIXED"


def _trajectory(rows: list[dict[str, Any]], getter) -> dict[str, Any]:
    values = [getter(row) for row in rows]
    clean = [v for v in values if v is not None]
    first = clean[0] if clean else None
    latest = clean[-1] if clean else None
    return {
        "values": [
            {"campaign": row["campaign"], "value": value}
            for row, value in zip(rows, values)
        ],
        "first": first,
        "latest": latest,
        "delta_first_to_latest": (
            None if first is None or latest is None else latest - first
        ),
        "direction": _direction(values),
    }


def _validation_calibration(health: dict[str, Any]) -> dict[str, Any]:
    events = []
    retentions: list[float] = []
    deltas: list[float] = []
    for row in health.get("forward_validation", []):
        dev = _float(row.get("selected_development_robust_sharpe"))
        forward = _float(row.get("selected_forward_sharpe_12"))
        retention = None
        if dev is not None and forward is not None and dev != 0:
            retention = forward / dev
            retentions.append(retention)
            deltas.append(forward - dev)
        events.append({
            "campaign": row.get("campaign"),
            "candidate": row.get("selected_development_candidate"),
            "decision": row.get("decision"),
            "development_robust_sharpe": dev,
            "forward_sharpe_12": forward,
            "retention_ratio": retention,
            "fold_status": row.get("fold_status"),
            "source_path": row.get("source_path"),
        })

    failed = sum(str(row.get("decision") or "").startswith("FAIL") for row in events)
    passed = sum(str(row.get("decision") or "").startswith("PASS") for row in events)
    return {
        "observed_gate_count": len(events),
        "failed_gate_count": failed,
        "passed_gate_count": passed,
        "failure_rate": _rate(failed, len(events)),
        "median_forward_to_development_retention": _median(retentions),
        "median_forward_minus_development_sharpe": _median(deltas),
        "events": events,
    }


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total_families = sum(row["family_count"] for row in rows)
    falsification = sum(row["falsification_coverage"]["count"] for row in rows)
    supported = sum(row["control_support"]["count"] for row in rows)
    economic = sum(row["economic_survival"]["count"] for row in rows)
    promotion = sum(row["promotion_ready"]["count"] for row in rows)
    resolved = sum(row["decision_resolution"]["count"] for row in rows)
    falsified = sum(row["falsified_by_controls_count"] for row in rows)
    supported_weak = sum(row["control_supported_but_weak_count"] for row in rows)

    all_names = [name for row in rows for name in row["family_names"]]
    unique_names = set(all_names)
    repeated = len(all_names) - len(unique_names)

    all_gap_counts = sum(
        row["research_to_dev"]["base_cells_compared"] for row in rows
    )
    all_nonnegative = sum(
        row["research_to_dev"]["nonnegative_gap_count"] for row in rows
    )

    return {
        "campaign_count": len(rows),
        "family_count": total_families,
        "falsification_coverage": {
            "count": falsification,
            "total": total_families,
            "rate": _rate(falsification, total_families),
        },
        "control_support": {
            "count": supported,
            "total": total_families,
            "rate": _rate(supported, total_families),
        },
        "economic_survival": {
            "count": economic,
            "total": total_families,
            "rate": _rate(economic, total_families),
        },
        "promotion_ready": {
            "count": promotion,
            "total": total_families,
            "rate": _rate(promotion, total_families),
        },
        "decision_resolution": {
            "count": resolved,
            "total": total_families,
            "rate": _rate(resolved, total_families),
        },
        "falsified_by_controls_count": falsified,
        "control_supported_but_weak_count": supported_weak,
        "exact_family_name_novelty": {
            "distinct_family_names": len(unique_names),
            "family_instances": len(all_names),
            "repeated_name_count": repeated,
            "repeated_name_rate": _rate(repeated, len(all_names)),
            "interpretation": (
                "Lexical family-name reuse only. This is a breadth proxy, not "
                "semantic originality or contest correlation evidence."
            ),
        },
        "research_to_dev": {
            "base_cells_compared": all_gap_counts,
            "nonnegative_gap_count": all_nonnegative,
            "nonnegative_gap_rate": _rate(all_nonnegative, all_gap_counts),
        },
    }


def _pooled_research_dev_gap(summaries: list[dict[str, Any]]) -> float | None:
    gaps: list[float] = []
    for summary in summaries:
        for cell in (summary.get("notable_base_cells") or {}).values():
            research = _float(cell.get("research_sharpe_12"))
            dev = _float(cell.get("dev_sharpe_12"))
            if research is not None and dev is not None:
                gaps.append(dev - research)
    return _median(gaps)


def _state_tags(rows: list[dict[str, Any]], aggregate: dict[str, Any], validation: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    if rows and all(row["falsification_coverage"]["rate"] == 1.0 for row in rows):
        tags.append("FALSIFICATION_DISCIPLINE_STABLE")
    bests = [row["best_robust_sharpe"] for row in rows]
    if len(bests) >= 2 and all(
        a is not None and b is not None and b < a
        for a, b in zip(bests, bests[1:])
    ):
        tags.append("ECONOMIC_FRONTIER_CONTRACTING")
    if (
        len(rows) >= 2
        and rows[0]["control_support"]["rate"] is not None
        and rows[-1]["control_support"]["rate"] is not None
        and rows[-1]["control_support"]["rate"] < rows[0]["control_support"]["rate"]
    ):
        tags.append("CAUSAL_SUPPORT_WEAKENING")
    gaps = [
        row["research_to_dev"]["median_dev_minus_research_sharpe_12"]
        for row in rows
    ]
    if gaps and all(gap is not None and gap < 0 for gap in gaps):
        tags.append("RESEARCH_TO_DEV_OPTIMISM_PERSISTS")
    if aggregate["promotion_ready"]["count"] == 0 and aggregate["family_count"] > 0:
        tags.append("PROMOTION_DROUGHT")
    retention = validation.get("median_forward_to_development_retention")
    if validation.get("failed_gate_count", 0) > 0 and retention is not None and retention < 1:
        tags.append("FORWARD_TRANSLATION_WEAK")
    return tags


def _next_actions(
    rows: list[dict[str, Any]],
    aggregate: dict[str, Any],
    validation: dict[str, Any],
    evidence_debt: dict[str, Any],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    queue_count = evidence_debt.get("measurement_queue_count") or 0
    if queue_count:
        actions.append({
            "priority": 1,
            "action": "MEASURE_FROZEN_QUEUE_FIRST",
            "why": (
                "A preregistered campaign is already frozen. Measure it unchanged "
                "before mutating hypotheses from newer diagnostics."
            ),
        })

    if (
        evidence_debt.get("summary_only_latest")
        or (evidence_debt.get("measured_campaigns_since_full_matrix") or 0) > 0
    ):
        actions.append({
            "priority": 2,
            "action": "DEEPEN_CANONICAL_MATRIX_EVIDENCE",
            "why": (
                "The measurement frontier is ahead of the latest full matrix; "
                "deepen evidence before the public surface drifts further."
            ),
        })

    pooled_gap = aggregate["research_to_dev"].get(
        "pooled_median_dev_minus_research_sharpe_12"
    )
    if pooled_gap is not None and pooled_gap < 0:
        actions.append({
            "priority": 3,
            "action": "TREAT_RESEARCH_FOLD_HIGHS_AS_OPTIMISTIC",
            "why": (
                "Recent base cells have a negative pooled median Dev−Research "
                "Sharpe gap. Demand stability evidence before spending more "
                "research budget on research-fold leaders."
            ),
        })

    retention = validation.get("median_forward_to_development_retention")
    if validation.get("failed_gate_count", 0) > 0 and retention is not None and retention < 1:
        actions.append({
            "priority": 4,
            "action": "CALIBRATE_DEVELOPMENT_CONFIDENCE",
            "why": (
                "Observed frozen forward validation retained only part of the "
                "development Sharpe. Keep development hits explicitly provisional."
            ),
        })

    bests = [row["best_robust_sharpe"] for row in rows]
    contracting = len(bests) >= 2 and all(
        a is not None and b is not None and b < a
        for a, b in zip(bests, bests[1:])
    )
    if contracting and aggregate["promotion_ready"]["count"] == 0:
        actions.append({
            "priority": 5,
            "action": "OPEN_DIFFERENT_OBJECT_CLASS_AFTER_QUEUE",
            "why": (
                "Recent best robust economics contracted across campaigns and no "
                "family reached the causal+economic intersection. After the frozen "
                "queue is measured, prefer a genuinely different alpha object over "
                "parameter rescue."
            ),
        })

    return actions


def build_payload() -> dict[str, Any]:
    health = _load_json(HEALTH, {})
    summaries = _recent_development_summaries()
    rows = [_campaign_row(summary) for summary in summaries]
    aggregate = _aggregate(rows)

    aggregate["research_to_dev"][
        "pooled_median_dev_minus_research_sharpe_12"
    ] = _pooled_research_dev_gap(summaries)

    validation = _validation_calibration(health)
    surface = health.get("surface_health", {})
    queue = health.get("learning_loop", {}).get("measurement_queue", {})
    evidence_debt = {
        "latest_full_matrix_campaign": surface.get("latest_full_matrix_campaign"),
        "latest_measured_campaign": health.get("latest_evidence", {}).get("campaign"),
        "latest_kind": health.get("latest_evidence", {}).get("kind"),
        "summary_only_latest": surface.get("summary_only_latest"),
        "measured_campaigns_since_full_matrix": surface.get(
            "measured_campaigns_since_full_matrix"
        ),
        "measurement_queue_count": queue.get("count"),
        "next_queued_campaign": (
            (queue.get("next_campaign") or {}).get("campaign")
            if isinstance(queue.get("next_campaign"), dict)
            else None
        ),
    }

    trajectories = {
        "best_robust_sharpe": _trajectory(
            rows, lambda row: row["best_robust_sharpe"]
        ),
        "control_support_rate": _trajectory(
            rows, lambda row: row["control_support"]["rate"]
        ),
        "median_central_control_margin": _trajectory(
            rows, lambda row: row["median_central_control_margin"]
        ),
        "median_dev_minus_research_sharpe_12": _trajectory(
            rows,
            lambda row: row["research_to_dev"][
                "median_dev_minus_research_sharpe_12"
            ],
        ),
    }

    tags = _state_tags(rows, aggregate, validation)
    actions = _next_actions(rows, aggregate, validation, evidence_debt)

    return {
        "schema_version": 1,
        "policy": {
            "aggregate_score": "FORBIDDEN",
            "cross_campaign_scalar_rank": "FORBIDDEN",
            "optimization_target": False,
            "purpose": "recursive-learning diagnostics, not a strategy objective",
            "missing_metrics": "remain missing; never imputed",
            "window_rule": f"latest {RECENT_WINDOW} canonical development summaries with family evidence",
        },
        "window_campaigns": [row["campaign"] for row in rows],
        "campaigns": rows,
        "recent_window": aggregate,
        "trajectories": trajectories,
        "validation_calibration": validation,
        "evidence_debt": evidence_debt,
        "state_tags": tags,
        "next_actions": actions,
    }


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _ratio(metric: dict[str, Any]) -> str:
    count = metric.get("count", 0)
    total = metric.get("total", 0)
    rate = metric.get("rate")
    suffix = "—" if rate is None else f"{100 * rate:.1f}%"
    return f"{count}/{total} ({suffix})"


def build_markdown(payload: dict[str, Any]) -> str:
    recent = payload["recent_window"]
    validation = payload["validation_calibration"]
    debt = payload["evidence_debt"]

    lines = [
        "---",
        "title: Recursive Learning",
        "description: Temporal dogfood telemetry for whether the Q25 research loop is becoming more informative, falsifiable, and transferable.",
        "---",
        "",
        "# Q25 recursive learning telemetry",
        "",
        "> No mega-score. No cross-campaign scalar ranking. These diagnostics measure the research process, not strategy quality.",
        "",
        "## Recent campaign window",
        "",
        f"Window: **{', '.join(payload['window_campaigns']) or '—'}**.",
        "",
        "| Campaign | Families | Falsification | Control support | Economic survival | Best robust SR | Median causal margin | Median Dev−Research SR |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for row in payload["campaigns"]:
        lines.append(
            f"| `{row['campaign']}` | {row['family_count']} | "
            f"{_ratio(row['falsification_coverage'])} | "
            f"{_ratio(row['control_support'])} | "
            f"{_ratio(row['economic_survival'])} | "
            f"{_fmt(row['best_robust_sharpe'])} | "
            f"{_fmt(row['median_central_control_margin'])} | "
            f"{_fmt(row['research_to_dev']['median_dev_minus_research_sharpe_12'])} |"
        )

    lines += [
        "",
        "## What the loop learned",
        "",
        f"- Falsification coverage: **{_ratio(recent['falsification_coverage'])}**.",
        f"- Control-supported mechanisms: **{_ratio(recent['control_support'])}**.",
        f"- Economic survivors: **{_ratio(recent['economic_survival'])}**.",
        f"- Promotion-ready causal+economic intersections: **{_ratio(recent['promotion_ready'])}**.",
        f"- Families falsified by destructive controls: **{recent['falsified_by_controls_count']}**.",
        f"- Control-supported but still economically weak families: **{recent['control_supported_but_weak_count']}**.",
        f"- Pooled median Dev−Research SR@12 gap across {recent['research_to_dev']['base_cells_compared']} comparable base cells: **{_fmt(recent['research_to_dev']['pooled_median_dev_minus_research_sharpe_12'])}**.",
        f"- Base cells with Dev SR@12 ≥ Research SR@12: **{recent['research_to_dev']['nonnegative_gap_count']}/{recent['research_to_dev']['base_cells_compared']}**.",
        "",
        "Exact family-name novelty is only a lexical breadth proxy; it is not semantic originality or contest-correlation evidence.",
        "",
        "## Trajectory",
        "",
    ]

    for name, metric in payload["trajectories"].items():
        lines.append(
            f"- **{name}**: {_fmt(metric['first'])} → {_fmt(metric['latest'])} "
            f"(Δ {_fmt(metric['delta_first_to_latest'])}; {metric['direction']})."
        )

    lines += [
        "",
        "## Validation calibration",
        "",
        f"Observed frozen forward gates: **{validation['observed_gate_count']}**; failures: **{validation['failed_gate_count']}**; passes: **{validation['passed_gate_count']}**.",
        f"Median forward/development retention: **{_fmt(validation['median_forward_to_development_retention'])}**.",
        f"Median forward−development Sharpe delta: **{_fmt(validation['median_forward_minus_development_sharpe'])}**.",
        "",
        "## Evidence debt",
        "",
        f"- Latest measured campaign: `{debt.get('latest_measured_campaign') or '—'}`.",
        f"- Latest full matrix: `{debt.get('latest_full_matrix_campaign') or '—'}`.",
        f"- Measured campaigns since full matrix: **{debt.get('measured_campaigns_since_full_matrix') or 0}**.",
        f"- Frozen measurement queue: **{debt.get('measurement_queue_count') or 0}**; next `{debt.get('next_queued_campaign') or '—'}`.",
        "",
        "## State tags",
        "",
    ]
    for tag in payload["state_tags"]:
        lines.append(f"- `{tag}`")

    lines += ["", "## Derived next actions", ""]
    for action in payload["next_actions"]:
        lines.append(
            f"- **P{action['priority']} {action['action']}** — {action['why']}"
        )

    lines += [
        "",
        "These actions are diagnostics derived from committed evidence. They do not rewrite frozen campaigns, reopen spent folds, or promote a strategy.",
        "",
    ]
    return "\n".join(lines)


def render() -> tuple[dict[str, Any], str]:
    payload = build_payload()
    return payload, build_markdown(payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    payload, markdown = render()
    text = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"

    if args.check:
        if not OUT_JSON.exists() or json.loads(OUT_JSON.read_text()) != payload:
            raise SystemExit("docs/data/recursive_learning.json is stale")
        if not OUT_MD.exists() or OUT_MD.read_text() != markdown:
            raise SystemExit("docs/RECURSIVE_LEARNING.md is stale")
        print("recursive learning telemetry is current")
        return

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(text)
    OUT_MD.write_text(markdown)
    print(OUT_JSON)
    print(OUT_MD)


if __name__ == "__main__":
    main()
