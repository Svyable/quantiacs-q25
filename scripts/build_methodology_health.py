#!/usr/bin/env python3
"""Build Q25 methodology-health and recursive-learning telemetry surfaces.

The renderer deliberately avoids a cross-campaign mega-score. It separates:

1. latest measured development evidence,
2. destructive-control pressure inside that campaign,
3. later validation evidence that can supersede an older development narrative,
4. evidence-depth / surface debt, and
5. preregistered campaigns that are ahead of the committed measurement frontier.

These are feedback channels for the research loop, not optimization targets. A new
piece of evidence should be able to make an older dashboard claim false, and the
builder should surface that conflict automatically instead of preserving stale text.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence"
EXPERIMENTS = ROOT / "experiments"
INDEX = ROOT / "docs" / "index.md"
RESEARCH_MATRIX = ROOT / "docs" / "RESEARCH_MATRIX.md"
DATA_OUT = ROOT / "docs" / "data" / "methodology_health.json"
MARKDOWN_OUT = ROOT / "docs" / "METHODOLOGY_HEALTH.md"
ROBUST_FLOOR = 1.0


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _rate(count: int, total: int) -> float | None:
    return None if total == 0 else count / total


def _campaign_entries() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for directory in sorted(EVIDENCE.glob("frontier_*")):
        if not directory.is_dir():
            continue
        sources = {
            "matrix": directory / "matrix.json",
            "summary": directory / "observed_summary.json",
            "observed": directory / "observed.json",
        }
        kinds = [name for name, path in sources.items() if path.exists()]
        if kinds:
            entries.append(
                {
                    "campaign": directory.name,
                    "kinds": kinds,
                    "paths": sources,
                }
            )
    return entries


def _latest_full_matrix(entries: list[dict[str, Any]]) -> str | None:
    campaigns = [entry["campaign"] for entry in entries if "matrix" in entry["kinds"]]
    return max(campaigns) if campaigns else None


def _campaigns_since_full_matrix(entries: list[dict[str, Any]]) -> int | None:
    full = _latest_full_matrix(entries)
    if full is None:
        return None
    return sum(1 for entry in entries if entry["campaign"] > full)


def _forward_validation_entries() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(EVIDENCE.glob("frontier_*/**/observed_summary.json")):
        payload = _load_json(path)
        stage = str(payload.get("evidence_stage") or "")
        if "FORWARD" not in stage and "validation_fold" not in payload:
            continue
        rows.append(
            {
                "campaign": payload.get("campaign") or path.parents[1].name,
                "family": payload.get("family"),
                "evidence_stage": payload.get("evidence_stage"),
                "fold_status": payload.get("fold_status"),
                "decision": payload.get("decision"),
                "selected_development_candidate": payload.get("selected_development_candidate"),
                "selected_development_robust_sharpe": _float_or_none(
                    payload.get("selected_development_robust_sharpe")
                ),
                "selected_forward_sharpe_12": _float_or_none(payload.get("selected_forward_sharpe_12")),
                "validation_fold": payload.get("validation_fold"),
                "source_path": str(path.relative_to(ROOT)),
            }
        )
    return rows


def _queued_campaigns(latest_measured: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(EXPERIMENTS.glob("frontier_*/manifest.json")):
        campaign = path.parent.name
        if campaign <= latest_measured:
            continue
        manifest = _load_json(path)
        candidates = list(manifest.get("candidates", []))
        families = sorted({str(row.get("family")) for row in candidates if row.get("family")})
        modes: dict[str, int] = {}
        for row in candidates:
            mode = str(row.get("mode") or "unknown")
            modes[mode] = modes.get(mode, 0) + 1
        rows.append(
            {
                "campaign": campaign,
                "candidate_count": len(candidates),
                "family_count": len(families),
                "families": families,
                "modes": modes,
                "automatic_promotion": manifest.get("automatic_promotion"),
                "selection_folds": manifest.get("selection_folds"),
                "classification_note": manifest.get("classification_note"),
                "source_path": str(path.relative_to(ROOT)),
            }
        )
    return rows


def _triage_summary(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family in summary.get("families", []):
        robust = _float_or_none(family.get("best_robust_sharpe"))
        if robust is None:
            continue
        central = _float_or_none(family.get("central_robust_sharpe"))
        ablation = _float_or_none(family.get("ablation_robust_sharpe"))
        falsifier = _float_or_none(family.get("falsifier_robust_sharpe"))
        control_values = [value for value in (ablation, falsifier) if value is not None]
        control_ceiling = max(control_values) if control_values else None
        falsification_complete = central is not None and ablation is not None and falsifier is not None
        central_control_margin = (
            central - control_ceiling
            if central is not None and control_ceiling is not None
            else None
        )
        control_supported = (
            central_control_margin > 0 if falsification_complete and central_control_margin is not None else None
        )
        rows.append(
            {
                "family": family.get("family"),
                "best_base_id": family.get("best_base_id"),
                "best_robust_sharpe": robust,
                "floor_margin": robust - ROBUST_FLOOR,
                "central_id": family.get("central_id"),
                "central_robust_sharpe": central,
                "ablation_robust_sharpe": ablation,
                "falsifier_robust_sharpe": falsifier,
                "control_ceiling": control_ceiling,
                "central_control_margin": central_control_margin,
                "falsification_complete": falsification_complete,
                "control_supported": control_supported,
                "decision_code": family.get("decision_code"),
                "guardrail_pass": robust >= ROBUST_FLOOR,
            }
        )

    # Transparent within-campaign triage only. No cross-campaign scalar.
    rows.sort(
        key=lambda row: (
            bool(row["guardrail_pass"]),
            float(row["best_robust_sharpe"]),
            str(row["family"]),
        ),
        reverse=True,
    )
    for rank, row in enumerate(rows, start=1):
        row["campaign_rank"] = rank
    return rows


def _reconcile_development_leader(
    leader: dict[str, Any] | None,
    validations: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not leader:
        return None
    out = dict(leader)
    candidate_id = leader.get("id")
    matching = [
        row for row in validations if row.get("selected_development_candidate") == candidate_id
    ]
    validation = matching[-1] if matching else None
    out["validation"] = validation
    if validation is None:
        out["state"] = "DEVELOPMENT_ONLY"
        out["active_after_validation"] = True
        return out

    decision = str(validation.get("decision") or "")
    if decision.startswith("FAIL"):
        state = "FAILED_FORWARD_GATE"
        active = False
    elif decision.startswith("PASS"):
        state = "PASSED_FORWARD_GATE"
        active = True
    else:
        state = decision or str(validation.get("evidence_stage") or "FORWARD_OBSERVED")
        active = False
    out["state"] = state
    out["active_after_validation"] = active
    return out


def _learning_loop(
    latest: dict[str, Any],
    health: dict[str, Any],
    leader: dict[str, Any] | None,
    queued: list[dict[str, Any]],
) -> dict[str, Any]:
    rows = latest["family_triage"]
    total = len(rows)
    falsification_count = sum(1 for row in rows if row["falsification_complete"])
    causal_count = sum(1 for row in rows if row["control_supported"] is True)
    economic_count = sum(1 for row in rows if row["guardrail_pass"])
    promotion_ready_count = sum(
        1 for row in rows if row["guardrail_pass"] and row["control_supported"] is True
    )
    resolved_count = sum(1 for row in rows if row.get("decision_code"))
    margins = [
        row["central_control_margin"]
        for row in rows
        if row["central_control_margin"] is not None
    ]
    best_robust = max((row["best_robust_sharpe"] for row in rows), default=None)

    validation = leader.get("validation") if leader else None
    next_boundary = str(latest.get("next_boundary") or "")
    guidance_superseded = bool(
        validation
        and leader
        and leader.get("id")
        and str(leader["id"]) in next_boundary
        and "forward" in next_boundary.lower()
    )

    return {
        "policy": {
            "aggregate_score": "forbidden",
            "purpose": "diagnostic feedback vector for the research loop",
            "optimization_target": False,
        },
        "latest_campaign": {
            "families_measured": total,
            "falsification_coverage": {
                "count": falsification_count,
                "total": total,
                "rate": _rate(falsification_count, total),
            },
            "causal_support": {
                "count": causal_count,
                "total": total,
                "rate": _rate(causal_count, total),
            },
            "economic_survival": {
                "count": economic_count,
                "total": total,
                "rate": _rate(economic_count, total),
            },
            "promotion_ready": {
                "count": promotion_ready_count,
                "total": total,
                "rate": _rate(promotion_ready_count, total),
            },
            "decision_resolution": {
                "count": resolved_count,
                "total": total,
                "rate": _rate(resolved_count, total),
            },
            "best_robust_sharpe": best_robust,
            "best_floor_margin": None if best_robust is None else best_robust - ROBUST_FLOOR,
            "median_central_control_margin": statistics.median(margins) if margins else None,
        },
        "validation_feedback": {
            "development_leader": leader.get("id") if leader else None,
            "state": leader.get("state") if leader else None,
            "active_after_validation": leader.get("active_after_validation") if leader else None,
            "forward_gate_decision": validation.get("decision") if validation else None,
            "forward_sharpe_12": validation.get("selected_forward_sharpe_12") if validation else None,
            "guidance_superseded_by_newer_validation": guidance_superseded,
        },
        "evidence_depth": {
            "latest_kind": latest["kind"],
            "summary_only_latest": health["summary_only_latest"],
            "latest_full_matrix_campaign": health.get("latest_full_matrix_campaign"),
            "measured_campaigns_since_full_matrix": health.get("measured_campaigns_since_full_matrix"),
        },
        "measurement_queue": {
            "count": len(queued),
            "next_campaign": queued[0] if queued else None,
            "campaigns": queued,
        },
    }


def build_payload() -> dict[str, Any]:
    entries = _campaign_entries()
    if not entries:
        raise RuntimeError("No measured frontier evidence found")

    latest = max(entries, key=lambda entry: entry["campaign"])
    campaign = latest["campaign"]
    summary_path = latest["paths"]["summary"]
    matrix_path = latest["paths"]["matrix"]

    if summary_path.exists():
        summary = _load_json(summary_path)
        triage = _triage_summary(summary)
        evidence_stage = summary.get("evidence_stage")
        decision = summary.get("decision")
        interpretation = summary.get("interpretation")
        declared_leader = summary.get("current_new_alpha_leader")
        evidence_kind = "summary_only" if not matrix_path.exists() else "matrix_and_summary"
    elif matrix_path.exists():
        matrix = _load_json(matrix_path)
        summary = {}
        triage = []
        evidence_stage = matrix.get("status")
        decision = None
        interpretation = None
        declared_leader = None
        evidence_kind = "matrix"
    else:
        raise RuntimeError(f"Latest campaign {campaign} has no supported evidence payload")

    index_text = INDEX.read_text() if INDEX.exists() else ""
    matrix_text = RESEARCH_MATRIX.read_text() if RESEARCH_MATRIX.exists() else ""
    validations = _forward_validation_entries()
    leader = _reconcile_development_leader(declared_leader, validations)
    queued = _queued_campaigns(campaign)

    health = {
        "latest_full_matrix_campaign": _latest_full_matrix(entries),
        "measured_campaigns_since_full_matrix": _campaigns_since_full_matrix(entries),
        "research_matrix_mentions_latest": campaign in matrix_text,
        "index_mentions_latest": campaign in index_text,
        "index_uses_generated_health": "methodology_health.json" in index_text,
        "summary_only_latest": evidence_kind == "summary_only",
    }

    latest_payload = {
        "campaign": campaign,
        "kind": evidence_kind,
        "evidence_stage": evidence_stage,
        "decision": decision,
        "family_count": len(triage),
        "family_triage": triage,
        "interpretation": interpretation,
        "next_boundary": summary.get("next_boundary"),
    }

    payload = {
        "schema_version": 2,
        "ranking_policy": {
            "cross_campaign_ranking": "forbidden",
            "within_campaign_order": [
                "guardrail_pass descending",
                "best_robust_sharpe descending",
                "family name deterministic tie-break",
            ],
            "robust_floor": ROBUST_FLOOR,
            "weighted_megascore": False,
            "missing_metrics": "remain missing; never imputed from related strategies",
        },
        "latest_evidence": latest_payload,
        "development_leader": leader,
        # Backward-compatible name; active_after_validation is authoritative.
        "surviving_development_seam": leader,
        "active_new_alpha_seam": leader if leader and leader.get("active_after_validation") else None,
        "forward_validation": validations,
        "surface_health": health,
    }
    payload["learning_loop"] = _learning_loop(latest_payload, health, leader, queued)
    return payload


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _ratio(metric: dict[str, Any]) -> str:
    return f"{metric['count']}/{metric['total']} ({100 * metric['rate']:.0f}%)" if metric.get("rate") is not None else "—"


def render() -> tuple[dict[str, Any], str]:
    payload = build_payload()
    latest = payload["latest_evidence"]
    health = payload["surface_health"]
    leader = payload.get("development_leader") or {}
    loop = payload["learning_loop"]
    loop_latest = loop["latest_campaign"]
    validation = loop["validation_feedback"]
    queue = loop["measurement_queue"]

    lines = [
        "# Methodology Health",
        "",
        "> Generated from committed evidence. This is a recursive feedback surface for the research process, not a cross-campaign leaderboard or an optimization score.",
        "",
        "## Evidence pulse",
        "",
        "| Check | State |",
        "|---|---|",
        f"| Latest measured campaign | `{latest['campaign']}` |",
        f"| Latest evidence tier | `{latest['kind']}` |",
        f"| Latest campaign decision | `{latest.get('decision') or '—'}` |",
        f"| Latest full matrix packet | `{health.get('latest_full_matrix_campaign') or '—'}` |",
        f"| Measured campaigns since full matrix | **{health.get('measured_campaigns_since_full_matrix') if health.get('measured_campaigns_since_full_matrix') is not None else '—'}** |",
        f"| Homepage bound to generated health JSON | **{'yes' if health['index_uses_generated_health'] else 'no'}** |",
        f"| Detailed research matrix includes latest | **{'yes' if health['research_matrix_mentions_latest'] else 'no — evidence-depth gap is explicit'}** |",
        "",
        "## Recursive learning telemetry",
        "",
        "These metrics are a **vector, not a score**. They are intended to make the next research action more informative while resisting reward hacking.",
        "",
        "| Feedback channel | Latest state | What it means |",
        "|---|---:|---|",
        f"| Falsification coverage | **{_ratio(loop_latest['falsification_coverage'])}** | families with central + ablation + destructive falsifier measurements |",
        f"| Causal support | **{_ratio(loop_latest['causal_support'])}** | central parent beats both matched destructive controls |",
        f"| Economic survival | **{_ratio(loop_latest['economic_survival'])}** | best base clears the fixed robust-development floor |",
        f"| Promotion-ready intersection | **{_ratio(loop_latest['promotion_ready'])}** | clears the floor **and** survives controls; still not validation |",
        f"| Decision resolution | **{_ratio(loop_latest['decision_resolution'])}** | measured families ended with an explicit decision code |",
        f"| Best floor margin | **{_fmt(loop_latest['best_floor_margin'])}** | best latest-family robust SR minus the fixed {ROBUST_FLOOR:.1f} floor |",
        f"| Median central-vs-control margin | **{_fmt(loop_latest['median_central_control_margin'])}** | positive is causal support; negative means a control matched/beat the parent |",
        "",
        "## Validation correction",
        "",
    ]

    if leader and leader.get("validation"):
        v = leader["validation"]
        lines.extend(
            [
                f"The earlier development leader **`{leader.get('id')}`** reported robust-development Sharpe **{_fmt(leader.get('robust_development_sharpe'))}**, but its frozen chronological validation is now observed.",
                "",
                f"- Forward gate: **`{v.get('decision')}`**",
                f"- Forward Sharpe @ 12% ATR-linked cost: **{_fmt(v.get('selected_forward_sharpe_12'))}**",
                f"- Validation fold: **{(v.get('validation_fold') or {}).get('start', '—')} → {(v.get('validation_fold') or {}).get('end', '—')}**",
                f"- Fold state: **`{v.get('fold_status') or '—'}`**",
                "",
            ]
        )
        if validation["guidance_superseded_by_newer_validation"]:
            lines.append(
                "The latest development summary's instruction to forward-test this seam is therefore **superseded by newer committed validation evidence**. The dashboard now self-corrects this conflict instead of preserving the stale development narrative."
            )
            lines.append("")
    elif leader:
        lines.append(
            f"`{leader.get('id')}` remains development-only; no later matching forward-validation packet was found."
        )
        lines.append("")
    else:
        lines.append("No development leader was declared by the latest packet.")
        lines.append("")

    lines.extend(
        [
            "## Measurement queue",
            "",
        ]
    )
    if queue["next_campaign"]:
        nxt = queue["next_campaign"]
        lines.extend(
            [
                f"The committed measurement frontier is ahead of the evidence frontier by **{queue['count']} preregistered campaign(s)**.",
                "",
                f"Next frozen campaign: **`{nxt['campaign']}`** — {nxt['candidate_count']} candidate/control cells across {nxt['family_count']} families; automatic promotion is `{nxt.get('automatic_promotion')}`.",
                "",
                nxt.get("classification_note") or "",
                "",
                "Until measured evidence is committed, this is a queue item—not a result. The useful recursive action is to measure or ingest the frozen packet unchanged, not mutate it because the dashboard is empty.",
                "",
            ]
        )
    else:
        lines.extend(["No preregistered campaign is currently ahead of the committed measurement frontier.", ""])

    lines.extend(
        [
            "## Latest-campaign family triage",
            "",
            "This ordering is valid **only inside the latest measured campaign**. Controls are shown beside economics so a high number cannot hide a broken causal story.",
            "",
            "| Rank | Family | Best base | Robust SR | Floor margin | Central | Control ceiling | Causal margin | Support | Decision |",
            "|---:|---|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )

    for row in latest["family_triage"]:
        support = "PASS" if row["control_supported"] is True else "FAIL" if row["control_supported"] is False else "—"
        lines.append(
            "| {rank} | `{family}` | `{best}` | {robust} | {floor_margin} | {central} | {ceiling} | {causal_margin} | {support} | `{decision}` |".format(
                rank=row["campaign_rank"],
                family=row["family"],
                best=row["best_base_id"],
                robust=_fmt(row["best_robust_sharpe"]),
                floor_margin=_fmt(row["floor_margin"]),
                central=_fmt(row["central_robust_sharpe"]),
                ceiling=_fmt(row["control_ceiling"]),
                causal_margin=_fmt(row["central_control_margin"]),
                support=support,
                decision=row["decision_code"],
            )
        )

    lines.extend(
        [
            "",
            "## Dogfood checks",
            "",
            "- **Newer evidence can invalidate older prose.** Forward-validation packets are reconciled against development-leader claims before rendering.",
            "- **Unmeasured work is visible but cannot masquerade as evidence.** Preregistered manifests ahead of the latest measured campaign appear only in the measurement queue.",
            "- **No cross-campaign scalar.** Strategy quality, causal support, validation state, evidence depth and queue state remain separate feedback channels.",
            "- **Missing packets stay missing.** Summary-only evidence is labeled as such instead of being expanded into synthetic matrix rows.",
            "- **CI remains the freshness alarm.** Tests compare this renderer with checked-in JSON/Markdown; the homepage reads the generated JSON directly.",
            "",
            "## Latest measured interpretation",
            "",
            latest.get("interpretation") or "No campaign interpretation was committed.",
            "",
        ]
    )

    if validation["guidance_superseded_by_newer_validation"]:
        lines.extend(
            [
                "### Superseding read-through",
                "",
                "The quoted interpretation above is preserved as historical development context, but its topology-forward-test recommendation is no longer current. The frozen forward packet failed its gate; the active recursive pressure is now the next preregistered, unmeasured campaign rather than another topology rescue.",
                "",
            ]
        )

    return payload, "\n".join(lines)


def main() -> None:
    payload, markdown = render()
    DATA_OUT.parent.mkdir(parents=True, exist_ok=True)
    DATA_OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    MARKDOWN_OUT.write_text(markdown)
    print(DATA_OUT.relative_to(ROOT))
    print(MARKDOWN_OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
