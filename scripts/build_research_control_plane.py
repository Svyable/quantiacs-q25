#!/usr/bin/env python3
"""Build a Q25 research control plane from committed evidence surfaces.

This is intentionally not a global strategy score. It keeps incompatible lanes
separate: frozen historical roster, latest comparable development campaign,
failed-forward candidates, measurement queue, measured-but-not-ingested receipts,
and reproducibility/evidence-health diagnostics.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
HEALTH = ROOT / "docs" / "data" / "methodology_health.json"
REPRO = ROOT / "docs" / "data" / "reproducibility_health.json"
HISTORICAL = ROOT / "configs" / "historical_top10.yaml"
RECEIPTS = ROOT / "evidence" / "measurement_receipts"
EXPERIMENTS = ROOT / "experiments"
OUT_JSON = ROOT / "docs" / "data" / "research_control_plane.json"
OUT_MD = ROOT / "docs" / "RESEARCH_CONTROL_PLANE.md"


def _load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text())


def _float(value: Any) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def _frontier_label(campaign: str) -> str | None:
    match = re.match(r"^frontier_\d{8}([a-z]+)(?:_|$)", str(campaign))
    return None if not match else f"Frontier-{match.group(1).upper()}"


def _receipt_rows() -> list[dict[str, Any]]:
    rows = []
    if not RECEIPTS.exists():
        return rows
    for path in sorted(RECEIPTS.glob("*.json")):
        payload = _load_json(path, {})
        campaign = payload.get("campaign") or path.stem
        canonical = ROOT / "evidence" / str(campaign) / "observed_summary.json"
        rows.append({
            "campaign": campaign,
            "frontier_label": _frontier_label(str(campaign)),
            "status": "CANONICAL_INGESTED" if canonical.exists() else "MEASURED_AWAITING_CANONICAL_INGEST",
            "decision": payload.get("decision"),
            "families": payload.get("families", []),
            "source": payload.get("source", {}),
            "source_path": str(path.relative_to(ROOT)),
        })
    return rows


def _queue_rows(health: dict[str, Any], receipts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    receipt_by_campaign = {row["campaign"]: row for row in receipts}
    queue = health.get("learning_loop", {}).get("measurement_queue", {}).get("campaigns", [])
    out = []
    for row in queue:
        item = dict(row)
        campaign = str(item.get("campaign"))
        receipt = receipt_by_campaign.get(campaign)
        item["frontier_label"] = _frontier_label(campaign)
        item["measurement_state"] = receipt["status"] if receipt else "FROZEN_UNMEASURED_OR_UNRECEIPTED"
        if receipt:
            item["measurement_receipt"] = receipt["source_path"]
            item["measured_decision"] = receipt.get("decision")
        out.append(item)
    return out


def _legacy_stack() -> list[dict[str, Any]]:
    historical = yaml.safe_load(HISTORICAL.read_text())
    rows = []
    for row in historical.get("strategies", []):
        rows.append({
            "rank": row.get("rank"),
            "id": row.get("id"),
            "name": row.get("name"),
            "role": row.get("role"),
            "full_sharpe": _float(row.get("full_sharpe")),
            "stress_sharpe": _float(row.get("stress_sharpe")),
            "stress_atr_fraction": _float(row.get("stress_atr_fraction")),
            "max_drawdown": _float(row.get("max_drawdown")),
            "status": row.get("status"),
            "lane": "FROZEN_HISTORICAL_ROSTER",
        })
    return rows


def _name_collisions(queue: list[dict[str, Any]], receipts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    campaigns = {str(row.get("campaign")) for row in queue}
    campaigns.update(str(row.get("campaign")) for row in receipts)
    for path in EXPERIMENTS.glob("frontier_*/manifest.json"):
        campaigns.add(path.parent.name)
    groups: dict[str, list[str]] = {}
    for campaign in campaigns:
        label = _frontier_label(campaign)
        if label:
            groups.setdefault(label, []).append(campaign)
    return [
        {"frontier_label": label, "campaigns": sorted(items), "severity": "WARN"}
        for label, items in sorted(groups.items()) if len(items) > 1
    ]


def build_payload() -> dict[str, Any]:
    health = _load_json(HEALTH, {})
    repro = _load_json(REPRO, {})
    receipts = _receipt_rows()
    queue = _queue_rows(health, receipts)
    latest = health.get("latest_evidence", {})
    leader = health.get("development_leader") or None
    surface = health.get("surface_health", {})
    collisions = _name_collisions(queue, receipts)

    pending_ingest = [row for row in receipts if row["status"] == "MEASURED_AWAITING_CANONICAL_INGEST"]
    unmeasured = [row for row in queue if row["measurement_state"] == "FROZEN_UNMEASURED_OR_UNRECEIPTED"]
    actions = []
    for row in pending_ingest:
        actions.append({"priority": 1, "action": "INGEST_MEASURED_EVIDENCE", "campaign": row["campaign"], "why": "A successful benchmark receipt exists but canonical observed evidence is not committed."})
    if collisions:
        actions.append({"priority": 2, "action": "DISAMBIGUATE_FRONTIER_LABELS", "campaign": None, "why": "Multiple campaign IDs map to the same human Frontier label; preserve historical IDs but display full campaign UID."})
    for row in unmeasured:
        actions.append({"priority": 3, "action": "MEASURE_FROZEN_CAMPAIGN", "campaign": row.get("campaign"), "why": "Frozen manifest is ahead of canonical evidence and has no committed measurement receipt."})
    if surface.get("summary_only_latest") or (surface.get("measured_campaigns_since_full_matrix") or 0) > 0:
        actions.append({"priority": 4, "action": "DEEPEN_MATRIX_EVIDENCE", "campaign": latest.get("campaign"), "why": "Latest committed campaign is not represented by a full canonical matrix packet."})
    actions.sort(key=lambda row: (row["priority"], str(row.get("campaign") or "")))

    latest_stack = []
    for row in latest.get("family_triage", []):
        latest_stack.append({
            "campaign_rank": row.get("campaign_rank"),
            "family": row.get("family"),
            "best_base_id": row.get("best_base_id"),
            "best_robust_sharpe": _float(row.get("best_robust_sharpe")),
            "floor_margin": _float(row.get("floor_margin")),
            "central_control_margin": _float(row.get("central_control_margin")),
            "control_supported": row.get("control_supported"),
            "decision_code": row.get("decision_code"),
            "lane": "LATEST_CANONICAL_DEVELOPMENT_CAMPAIGN",
        })

    failed_forward = []
    if leader and leader.get("active_after_validation") is False:
        validation = leader.get("validation") or {}
        failed_forward.append({
            "id": leader.get("id"),
            "development_robust_sharpe": _float(leader.get("robust_development_sharpe")),
            "forward_sharpe_12": _float(validation.get("selected_forward_sharpe_12")),
            "decision": validation.get("decision") or leader.get("state"),
            "state": leader.get("state"),
            "lane": "FAILED_OR_RETIRED_FORWARD_EVIDENCE",
        })

    return {
        "schema_version": 1,
        "policy": {"cross_campaign_scalar_rank": "FORBIDDEN", "weighted_mega_score": False, "lane_order_is_not_quality_order": True, "missing_metrics": "remain missing", "display_rule": "show campaign UID whenever human Frontier labels collide"},
        "canonical_latest": {"campaign": latest.get("campaign"), "frontier_label": _frontier_label(str(latest.get("campaign") or "")), "kind": latest.get("kind"), "decision": latest.get("decision"), "family_stack": latest_stack},
        "frozen_historical_stack": _legacy_stack(),
        "failed_forward_stack": failed_forward,
        "measurement_queue": queue,
        "measurement_receipts": receipts,
        "surface_debt": {"latest_full_matrix_campaign": surface.get("latest_full_matrix_campaign"), "measured_campaigns_since_full_matrix": surface.get("measured_campaigns_since_full_matrix"), "summary_only_latest": surface.get("summary_only_latest"), "research_matrix_mentions_latest": surface.get("research_matrix_mentions_latest")},
        "reproducibility": {"campaign": repro.get("campaign"), "status": repro.get("status"), "decision_stable_count": repro.get("summary", {}).get("decision_stable_count"), "families_compared": repro.get("summary", {}).get("families_compared"), "max_abs_summary_metric_delta": repro.get("summary", {}).get("max_abs_summary_metric_delta")},
        "dogfood": {"frontier_label_collisions": collisions, "pending_canonical_ingest_count": len(pending_ingest), "unmeasured_queue_count": len(unmeasured), "next_actions": actions},
    }


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def build_markdown(payload: dict[str, Any]) -> str:
    latest = payload["canonical_latest"]
    dogfood = payload["dogfood"]
    lines = ["---", "title: Research Control Plane", "description: Lane-separated strategy stack, evidence frontier, measurement queue, and dogfood diagnostics.", "---", "", "# Q25 research control plane", "", "> This is a control plane, not a mega-score. Historical, development, forward-validation, and queued evidence stay in separate lanes.", "", "## Canonical latest development campaign", "", f"**{latest.get('campaign') or '—'}** · {latest.get('decision') or '—'} · evidence `{latest.get('kind') or '—'}`", "", "| Local rank | Family | Best base | Robust SR | Floor margin | Causal margin | Support | Decision |", "|---:|---|---|---:|---:|---:|---|---|"]
    for row in latest.get("family_stack", []):
        support = "PASS" if row.get("control_supported") is True else "FAIL" if row.get("control_supported") is False else "—"
        lines.append(f"| {row.get('campaign_rank') or '—'} | {row.get('family') or '—'} | `{row.get('best_base_id') or '—'}` | {_fmt(row.get('best_robust_sharpe'))} | {_fmt(row.get('floor_margin'))} | {_fmt(row.get('central_control_margin'))} | {support} | {row.get('decision_code') or '—'} |")

    lines += ["", "## Frozen historical stack", "", "Frozen roster order is preserved from its dated evidence. It is not cross-ranked against modern development packets.", "", "| Frozen rank | Strategy | Role | Full SR | Stress SR | Max DD | Status |", "|---:|---|---|---:|---:|---:|---|"]
    for row in payload["frozen_historical_stack"]:
        stress = "—" if row["stress_sharpe"] is None else f"{row['stress_sharpe']:.3f} @ {100 * row['stress_atr_fraction']:.0f}% ATR"
        dd = "—" if row["max_drawdown"] is None else f"{100 * row['max_drawdown']:.1f}%"
        lines.append(f"| {row['rank']} | {row['name']} | {row['role']} | {_fmt(row['full_sharpe'])} | {stress} | {dd} | {row['status']} |")

    lines += ["", "## Measurement frontier", "", "| Campaign UID | Display label | State | Families | Cells | Measured decision |", "|---|---|---|---:|---:|---|"]
    for row in payload["measurement_queue"]:
        lines.append(f"| `{row.get('campaign')}` | {row.get('frontier_label') or '—'} | {row.get('measurement_state')} | {row.get('family_count', '—')} | {row.get('candidate_count', '—')} | {row.get('measured_decision') or '—'} |")
    if not payload["measurement_queue"]:
        lines.append("| — | — | queue clear | 0 | 0 | — |")

    lines += ["", "## Dogfood diagnostics", "", f"Pending canonical evidence ingestion: **{dogfood['pending_canonical_ingest_count']}**. Frozen/unreceipted campaigns: **{dogfood['unmeasured_queue_count']}**.", ""]
    if dogfood["frontier_label_collisions"]:
        for collision in dogfood["frontier_label_collisions"]:
            lines.append(f"- **{collision['severity']} {collision['frontier_label']} collision:** " + ", ".join(f"`{x}`" for x in collision["campaigns"]) + ". Display full campaign UID; do not rename historical evidence.")
    else:
        lines.append("- No human Frontier-label collisions detected.")
    for action in dogfood["next_actions"]:
        campaign = f" `{action['campaign']}`" if action.get("campaign") else ""
        lines.append(f"- **P{action['priority']} {action['action']}**{campaign}: {action['why']}")

    repro = payload["reproducibility"]
    lines += ["", "## Reproducibility context", "", f"Latest replay-health packet: `{repro.get('campaign') or '—'}` · **{repro.get('status') or '—'}**. Decision-stable families: {repro.get('decision_stable_count') or 0}/{repro.get('families_compared') or 0}; max compared summary-metric delta: {_fmt(repro.get('max_abs_summary_metric_delta'), 9)}.", "", "The control plane never averages metrics across provenance contexts.", ""]
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
            raise SystemExit("docs/data/research_control_plane.json is stale")
        if not OUT_MD.exists() or OUT_MD.read_text() != markdown:
            raise SystemExit("docs/RESEARCH_CONTROL_PLANE.md is stale")
        print("research control plane is current")
        return
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(text)
    OUT_MD.write_text(markdown)
    print(OUT_JSON)
    print(OUT_MD)


if __name__ == "__main__":
    main()
