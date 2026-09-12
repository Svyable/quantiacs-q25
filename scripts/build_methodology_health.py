#!/usr/bin/env python3
"""Build the Q25 methodology-health and latest-campaign triage surfaces.

This deliberately does *not* create a cross-campaign mega-score. It answers three
separate questions from committed evidence:

1. What is the latest measured campaign?
2. How did the families inside that campaign triage under the declared robust floor?
3. What older development seam is still alive according to the latest packet?

The checked-in artifacts are compared against render() in tests. A new evidence
campaign therefore makes CI fail until the public surface is regenerated, which
lets the repository dogfood its own evidence discipline.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence"
INDEX = ROOT / "docs" / "index.md"
RESEARCH_MATRIX = ROOT / "docs" / "RESEARCH_MATRIX.md"
DATA_OUT = ROOT / "docs" / "data" / "methodology_health.json"
MARKDOWN_OUT = ROOT / "docs" / "METHODOLOGY_HEALTH.md"
ROBUST_FLOOR = 1.0


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text())


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


def _triage_summary(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family in summary.get("families", []):
        robust = family.get("best_robust_sharpe")
        if robust is None:
            continue
        rows.append(
            {
                "family": family.get("family"),
                "best_base_id": family.get("best_base_id"),
                "best_robust_sharpe": float(robust),
                "central_id": family.get("central_id"),
                "central_robust_sharpe": family.get("central_robust_sharpe"),
                "ablation_robust_sharpe": family.get("ablation_robust_sharpe"),
                "falsifier_robust_sharpe": family.get("falsifier_robust_sharpe"),
                "decision_code": family.get("decision_code"),
                "guardrail_pass": float(robust) >= ROBUST_FLOOR,
            }
        )

    # A transparent lexicographic triage, not a weighted score. This ordering is
    # valid only *inside this one campaign*.
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
        surviving = summary.get("current_new_alpha_leader")
        evidence_kind = "summary_only" if not matrix_path.exists() else "matrix_and_summary"
    elif matrix_path.exists():
        matrix = _load_json(matrix_path)
        summary = {}
        triage = []
        evidence_stage = matrix.get("status")
        decision = None
        interpretation = None
        surviving = None
        evidence_kind = "matrix"
    else:
        raise RuntimeError(f"Latest campaign {campaign} has no supported evidence payload")

    index_text = INDEX.read_text() if INDEX.exists() else ""
    matrix_text = RESEARCH_MATRIX.read_text() if RESEARCH_MATRIX.exists() else ""

    return {
        "schema_version": 1,
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
        "latest_evidence": {
            "campaign": campaign,
            "kind": evidence_kind,
            "evidence_stage": evidence_stage,
            "decision": decision,
            "family_count": len(triage),
            "family_triage": triage,
            "interpretation": interpretation,
        },
        "surviving_development_seam": surviving,
        "surface_health": {
            "latest_full_matrix_campaign": _latest_full_matrix(entries),
            "research_matrix_mentions_latest": campaign in matrix_text,
            "index_mentions_latest": campaign in index_text,
            "summary_only_latest": evidence_kind == "summary_only",
        },
    }


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def render() -> tuple[dict[str, Any], str]:
    payload = build_payload()
    latest = payload["latest_evidence"]
    health = payload["surface_health"]
    leader = payload.get("surviving_development_seam") or {}

    lines = [
        "# Methodology Health",
        "",
        "> Generated from committed evidence. This is a control surface for the research process, not a cross-campaign leaderboard.",
        "",
        "## Evidence pulse",
        "",
        "| Check | State |",
        "|---|---|",
        f"| Latest measured campaign | `{latest['campaign']}` |",
        f"| Latest evidence tier | `{latest['kind']}` |",
        f"| Latest campaign decision | `{latest.get('decision') or '—'}` |",
        f"| Latest full matrix packet | `{health.get('latest_full_matrix_campaign') or '—'}` |",
        f"| Detailed research matrix includes latest | **{'yes' if health['research_matrix_mentions_latest'] else 'no — gap is explicit'}** |",
        f"| Dashboard index includes latest | **{'yes' if health['index_mentions_latest'] else 'no'}** |",
        "",
        "The detailed matrix and this health surface intentionally have different evidence tiers. A summary-only campaign is shown here rather than silently inventing matrix rows that were never committed.",
        "",
        "## Latest-campaign family triage",
        "",
        "This ordering is valid **only inside the latest campaign**. Families first have to clear the fixed robust-development floor; ties are then ordered by measured robust Sharpe. No weighted mega-score is used.",
        "",
        "| Rank | Family | Best base | Robust SR | Floor ≥1.0 | Decision | Central | Ablation | Falsifier |",
        "|---:|---|---|---:|---:|---|---:|---:|---:|",
    ]

    for row in latest["family_triage"]:
        lines.append(
            "| {rank} | `{family}` | `{best}` | {robust} | {gate} | `{decision}` | {central} | {ablation} | {falsifier} |".format(
                rank=row["campaign_rank"],
                family=row["family"],
                best=row["best_base_id"],
                robust=_fmt(row["best_robust_sharpe"]),
                gate="PASS" if row["guardrail_pass"] else "FAIL",
                decision=row["decision_code"],
                central=_fmt(row["central_robust_sharpe"]),
                ablation=_fmt(row["ablation_robust_sharpe"]),
                falsifier=_fmt(row["falsifier_robust_sharpe"]),
            )
        )

    lines.extend(
        [
            "",
            "## Surviving development seam",
            "",
        ]
    )
    if leader:
        lines.extend(
            [
                f"The latest packet still identifies **`{leader.get('id')}`** as the surviving new-alpha seam, with a reported robust-development Sharpe of **{_fmt(leader.get('robust_development_sharpe'))}** in its earlier evidence packet.",
                "",
                f"> {leader.get('note', '')}".rstrip(),
            ]
        )
    else:
        lines.append("No surviving development seam was declared by the latest packet.")

    lines.extend(
        [
            "",
            "## Dogfood checks",
            "",
            "- **Recency is not rank.** The newest campaign can fail while an older, separately measured seam remains alive.",
            "- **No cross-campaign scalar.** Sponsor snapshots and evidence stages stay separate; the renderer refuses to manufacture one global score.",
            "- **Missing packets stay missing.** Summary-only evidence is labeled as such instead of being expanded into synthetic matrix rows.",
            "- **CI is the freshness alarm.** Tests compare this renderer with the checked-in JSON/Markdown, so the next committed campaign makes the surface stale until it is regenerated.",
            "- **Controls remain visible.** Parent, ablation and falsifier results sit beside the family rank so a high number cannot hide failed causality/economic controls.",
            "",
            "## Current interpretation",
            "",
            latest.get("interpretation") or "No campaign interpretation was committed.",
            "",
            "The next iteration should attack the surviving seam with preregistered, causally distinct repairs and forward-safe diagnostics—not tune the latest failed families after observation.",
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
