#!/usr/bin/env python3
"""Build methodology-health surfaces from committed frontier evidence.

The renderer is intentionally evidence-schema tolerant but ranking-policy strict:
latest-campaign triage is local to one comparable packet, cross-campaign scalar
ranking is forbidden, and missing metrics remain missing.
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
    entries = []
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
            entries.append({"campaign": directory.name, "kinds": kinds, "paths": sources})
    return entries


def _latest_full_matrix(entries: list[dict[str, Any]]) -> str | None:
    campaigns = [e["campaign"] for e in entries if "matrix" in e["kinds"]]
    return max(campaigns) if campaigns else None


def _declared_survivor(entries: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return the most recent *structured* surviving seam declaration, if any."""
    for entry in sorted(entries, key=lambda e: e["campaign"], reverse=True):
        path = entry["paths"]["summary"]
        if not path.exists():
            continue
        summary = _load_json(path)
        survivor = summary.get("current_new_alpha_leader")
        if survivor:
            result = dict(survivor)
            result.setdefault("declared_in_campaign", entry["campaign"])
            return result
    return None


def _best_notable(summary: dict[str, Any], family: str) -> tuple[str | None, float | None]:
    cells = summary.get("notable_base_cells", {})
    candidates = []
    for cid, metrics in cells.items():
        if cid.startswith(family + "_") and metrics.get("robust_sharpe") is not None:
            candidates.append((cid, float(metrics["robust_sharpe"])))
    return max(candidates, key=lambda x: (x[1], x[0])) if candidates else (None, None)


def _triage_summary(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    if summary.get("families"):
        for family in summary["families"]:
            robust = family.get("best_robust_sharpe")
            if robust is None:
                continue
            rows.append({
                "family": family.get("family"),
                "best_base_id": family.get("best_base_id"),
                "best_robust_sharpe": float(robust),
                "central_id": family.get("central_id"),
                "central_robust_sharpe": family.get("central_robust_sharpe"),
                "ablation_robust_sharpe": family.get("ablation_robust_sharpe"),
                "falsifier_robust_sharpe": family.get("falsifier_robust_sharpe"),
                "decision_code": family.get("decision_code"),
            })
    else:
        for family in summary.get("family_decisions", []):
            name = family.get("family")
            best_id, notable_score = _best_notable(summary, name)
            robust = family.get("best_score")
            if robust is None:
                robust = notable_score
            if robust is None:
                continue
            central_id = f"{name}_w63" if f"{name}_w63" in summary.get("notable_base_cells", {}) else None
            central = summary.get("notable_base_cells", {}).get(central_id or "", {}).get("robust_sharpe")
            rows.append({
                "family": name,
                "best_base_id": best_id,
                "best_robust_sharpe": float(robust),
                "central_id": central_id,
                "central_robust_sharpe": central,
                "ablation_robust_sharpe": None,
                "falsifier_robust_sharpe": None,
                "decision_code": family.get("decision_code"),
            })

    for row in rows:
        row["guardrail_pass"] = float(row["best_robust_sharpe"]) >= ROBUST_FLOOR
    rows.sort(key=lambda r: (bool(r["guardrail_pass"]), float(r["best_robust_sharpe"]), str(r["family"])), reverse=True)
    for rank, row in enumerate(rows, 1):
        row["campaign_rank"] = rank
    return rows


def build_payload() -> dict[str, Any]:
    entries = _campaign_entries()
    if not entries:
        raise RuntimeError("No measured frontier evidence found")
    latest = max(entries, key=lambda e: e["campaign"])
    campaign = latest["campaign"]
    summary_path = latest["paths"]["summary"]
    matrix_path = latest["paths"]["matrix"]

    if summary_path.exists():
        summary = _load_json(summary_path)
        triage = _triage_summary(summary)
        evidence_stage = summary.get("evidence_stage") or summary.get("status")
        decision = summary.get("decision")
        interpretation = summary.get("interpretation") or summary.get("next_boundary")
        evidence_kind = "summary_only" if not matrix_path.exists() else "matrix_and_summary"
    elif matrix_path.exists():
        matrix = _load_json(matrix_path)
        triage = []
        evidence_stage = matrix.get("status")
        decision = None
        interpretation = None
        evidence_kind = "matrix"
    else:
        raise RuntimeError(f"Latest campaign {campaign} has no supported evidence payload")

    index_text = INDEX.read_text() if INDEX.exists() else ""
    matrix_text = RESEARCH_MATRIX.read_text() if RESEARCH_MATRIX.exists() else ""
    return {
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
        "latest_evidence": {
            "campaign": campaign,
            "kind": evidence_kind,
            "evidence_stage": evidence_stage,
            "decision": decision,
            "family_count": len(triage),
            "family_triage": triage,
            "interpretation": interpretation,
        },
        "surviving_development_seam": _declared_survivor(entries),
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
        "# Methodology Health", "",
        "> Generated from committed evidence. This is a control surface for the research process, not a cross-campaign leaderboard.", "",
        "## Evidence pulse", "",
        "| Check | State |", "|---|---|",
        f"| Latest measured campaign | `{latest['campaign']}` |",
        f"| Latest evidence tier | `{latest['kind']}` |",
        f"| Latest campaign decision | `{latest.get('decision') or '—'}` |",
        f"| Latest full matrix packet | `{health.get('latest_full_matrix_campaign') or '—'}` |",
        f"| Detailed research matrix includes latest | **{'yes' if health['research_matrix_mentions_latest'] else 'no — gap is explicit'}** |",
        f"| Dashboard index includes latest | **{'yes' if health['index_mentions_latest'] else 'no'}** |", "",
        "The detailed matrix and this health surface intentionally have different evidence tiers. A summary-only campaign is shown here rather than silently inventing matrix rows that were never committed.", "",
        "## Latest-campaign family triage", "",
        "This ordering is valid **only inside the latest campaign**. Families first have to clear the fixed robust-development floor; ties are then ordered by measured robust Sharpe. No weighted mega-score is used.", "",
        "| Rank | Family | Best base | Robust SR | Floor ≥1.0 | Decision | Central | Ablation | Falsifier |",
        "|---:|---|---|---:|---:|---|---:|---:|---:|",
    ]
    for row in latest["family_triage"]:
        lines.append("| {rank} | `{family}` | `{best}` | {robust} | {gate} | `{decision}` | {central} | {ablation} | {falsifier} |".format(
            rank=row["campaign_rank"], family=row["family"], best=row["best_base_id"] or "—",
            robust=_fmt(row["best_robust_sharpe"]), gate="PASS" if row["guardrail_pass"] else "FAIL",
            decision=row["decision_code"], central=_fmt(row["central_robust_sharpe"]),
            ablation=_fmt(row["ablation_robust_sharpe"]), falsifier=_fmt(row["falsifier_robust_sharpe"])))
    lines += ["", "## Surviving development seam", ""]
    if leader:
        source = leader.get("declared_in_campaign")
        provenance = f" Structured declaration from `{source}`." if source else ""
        lines += [
            f"The most recent structured packet that names a survivor identifies **`{leader.get('id')}`** with reported robust-development Sharpe **{_fmt(leader.get('robust_development_sharpe'))}**.{provenance}", "",
            f"> {leader.get('note', '')}".rstrip(),
        ]
    else:
        lines.append("No structured surviving development seam is present in committed packets.")
    lines += [
        "", "## Dogfood checks", "",
        "- **Recency is not rank.** The newest campaign can fail while an older, separately measured seam remains alive.",
        "- **Evidence schemas are normalized, not guessed.** Known committed summary schemas map into one control surface; absent metrics remain absent.",
        "- **No cross-campaign scalar.** Sponsor snapshots and evidence stages stay separate; the renderer refuses to manufacture one global score.",
        "- **Missing packets stay missing.** Summary-only evidence is labeled as such instead of being expanded into synthetic matrix rows.",
        "- **CI is the freshness alarm.** Tests compare this renderer with checked-in JSON/Markdown, so new evidence makes the surface stale until regenerated.",
        "- **Controls remain visible when structured.** Parent, ablation and falsifier metrics are displayed when the packet actually contains them.",
        "", "## Current interpretation", "", latest.get("interpretation") or "No campaign interpretation was committed.", "",
        "The next iteration should follow the latest packet's declared boundary and preregister any new mutation before return inspection.", "",
    ]
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
