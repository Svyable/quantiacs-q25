#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RECURSIVE = ROOT / "docs" / "data" / "recursive_learning.json"
CONTROL = ROOT / "docs" / "data" / "research_control_plane.json"
OUT_JSON = ROOT / "docs" / "data" / "learning_router.json"
OUT_MD = ROOT / "docs" / "LEARNING_ROUTER.md"

PIPELINE_ACTIONS = {"INGEST_MEASURED_EVIDENCE","MEASURE_FROZEN_CAMPAIGN","DEEPEN_MATRIX_EVIDENCE"}

def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())

def _ratio(metric: dict[str, Any] | None) -> dict[str, Any]:
    metric = metric or {}
    return {"count": metric.get("count"), "total": metric.get("total"), "rate": metric.get("rate")}

def _pipeline(control: dict[str, Any]) -> dict[str, Any]:
    queue = control.get("measurement_queue", [])
    pending_ingest = [
        {"campaign": row.get("campaign"), "measured_decision": row.get("measured_decision"), "family_count": row.get("family_count")}
        for row in queue if row.get("measurement_state") == "MEASURED_AWAITING_CANONICAL_INGEST"
    ]
    unmeasured = [
        {"campaign": row.get("campaign"), "family_count": row.get("family_count")}
        for row in queue if row.get("measurement_state") == "FROZEN_UNMEASURED_OR_UNRECEIPTED"
    ]
    operational = [row for row in control.get("dogfood", {}).get("next_actions", []) if row.get("action") in PIPELINE_ACTIONS]
    operational.sort(key=lambda row: (row.get("priority",999), str(row.get("campaign") or "")))
    latest = control.get("canonical_latest", {})
    canonical_latest = {
        "campaign": latest.get("campaign"),
        "decision": latest.get("decision"),
        "kind": latest.get("kind"),
    }
    if pending_ingest:
        bottleneck = {"stage":"CANONICAL_INGEST","count":len(pending_ingest),"campaigns":[row["campaign"] for row in pending_ingest],"reason":"Measured evidence exists but the canonical evidence frontier has not absorbed it yet."}
    elif unmeasured:
        bottleneck = {"stage":"MEASUREMENT","count":len(unmeasured),"campaigns":[row["campaign"] for row in unmeasured],"reason":"Frozen experiments exist without committed measurement receipts."}
    elif control.get("surface_debt", {}).get("summary_only_latest"):
        bottleneck = {"stage":"EVIDENCE_DEPTH","count":control.get("surface_debt", {}).get("measured_campaigns_since_full_matrix") or 0,"campaigns":[canonical_latest.get("campaign")],"reason":"Canonical measurement is ahead of the latest full matrix packet."}
    else:
        bottleneck = {"stage":"CLEAR","count":0,"campaigns":[],"reason":"No ingestion, measurement, or matrix-depth bottleneck is currently encoded."}
    return {
        "canonical_latest": canonical_latest,
        "pending_canonical_ingest": pending_ingest,
        "frozen_unmeasured": unmeasured,
        "failed_forward_count": len(control.get("failed_forward_stack", [])),
        "surface_debt": control.get("surface_debt", {}),
        "bottleneck": bottleneck,
        "operational_actions": operational,
    }

def _beliefs(recursive: dict[str, Any], pipeline: dict[str, Any]) -> list[dict[str, Any]]:
    recent = recursive.get("recent_window", {})
    r2d = recent.get("research_to_dev", {})
    validation = recursive.get("validation_calibration", {})
    beliefs = []
    support = _ratio(recent.get("control_support"))
    beliefs.append({"id":"causal_yield","state":"LOW_POSITIVE_YIELD" if (support.get("count") or 0)>0 else "NO_POSITIVE_YIELD","evidence":f"{support.get('count') or 0}/{support.get('total') or 0} recent families beat matched destructive controls.","uncertainty":"Development-only evidence; control support is not forward validation."})
    economic = _ratio(recent.get("economic_survival"))
    beliefs.append({"id":"economic_yield","state":"NO_RECENT_SURVIVORS" if (economic.get("count") or 0)==0 else "RECENT_SURVIVORS_EXIST","evidence":f"{economic.get('count') or 0}/{economic.get('total') or 0} recent families clear the fixed robust-development floor.","uncertainty":"The recent window is bounded and is not a claim about all historical strategies."})
    gap = r2d.get("pooled_median_dev_minus_research_sharpe_12"); held=r2d.get("nonnegative_gap_count"); compared=r2d.get("base_cells_compared")
    beliefs.append({"id":"selection_transfer","state":"RESEARCH_OPTIMISM_OBSERVED" if gap is not None and gap<0 else "NO_NEGATIVE_MEDIAN_GAP","evidence":f"Median Dev−Research SR@12 is {gap:.3f}; {held}/{compared} comparable cells held or improved." if gap is not None else "Comparable research-to-development gap is missing.","uncertainty":"This describes the recent comparable cells, not a universal shrinkage coefficient."})
    observed=validation.get("observed_gate_count") or 0; failed=validation.get("failed_gate_count") or 0; retention=validation.get("median_forward_to_development_retention")
    beliefs.append({"id":"forward_translation","state":"ONE_OBSERVED_FAILURE" if observed==1 and failed==1 else ("MIXED_OR_MULTIPLE_GATES" if observed else "NO_OBSERVED_GATES"),"evidence":f"{failed}/{observed} observed frozen forward gates failed; retention {retention:.1%}." if observed and retention is not None else f"{failed}/{observed} observed frozen forward gates failed.","uncertainty":"A single forward event is a calibration warning, not a population estimate."})
    bottleneck=pipeline["bottleneck"]
    beliefs.append({"id":"evidence_freshness","state":f"{bottleneck['stage']}_BOTTLENECK" if bottleneck["stage"]!="CLEAR" else "PIPELINE_CLEAR","evidence":bottleneck["reason"],"uncertainty":"Pipeline state is derived from committed repository artifacts only."})
    return beliefs

def _router(recursive: dict[str, Any], pipeline: dict[str, Any]) -> dict[str, Any]:
    actions=pipeline["operational_actions"]; next_action=actions[0] if actions else None; after=actions[1:] if len(actions)>1 else []
    promotion=recursive.get("recent_window", {}).get("promotion_ready", {}); tags=set(recursive.get("state_tags", []))
    invention_status="BLOCKED_BY_EXISTING_EVIDENCE_WORK"; invention_reason="Finish higher-priority ingestion / measurement / evidence-depth work before opening another mutable campaign."
    if not actions:
        if (promotion.get("count") or 0)==0 and "ECONOMIC_FRONTIER_CONTRACTING" in tags:
            invention_status="NEW_OBJECT_CLASS_JUSTIFIED"; invention_reason="No pipeline work remains and the recent causal+economic frontier has not produced a promotion-ready family."
        else:
            invention_status="REASSESS_AFTER_CURRENT_EVIDENCE"; invention_reason="No deterministic pipeline action remains; inspect current evidence state before allocating new hypothesis budget."
    return {"next_action":next_action,"current_state_backlog":after,"new_hypothesis_budget":{"state":invention_status,"why":invention_reason},"mutation_guardrail":"Never retune a frozen or measured campaign to answer diagnostics produced by its own returns."}

def build_payload() -> dict[str, Any]:
    recursive=_load(RECURSIVE); control=_load(CONTROL); pipeline=_pipeline(control)
    return {"schema_version":1,"policy":{"aggregate_score":"FORBIDDEN","strategy_ranking":"OUT_OF_SCOPE","optimization_target":False,"purpose":"route research work by evidence stage and belief uncertainty"},"pipeline":pipeline,"belief_updates":_beliefs(recursive,pipeline),"router":_router(recursive,pipeline)}

def build_markdown(payload: dict[str, Any]) -> str:
    p=payload["pipeline"]; r=payload["router"]
    lines=["---","title: Learning Router","description: Evidence-stage router for recursive Q25 research work.","---","","# Q25 learning router","","> The router does not score strategies. It decides what type of research work is currently justified by committed evidence.","","## Pipeline","",f"- Canonical latest: `{p.get('canonical_latest',{}).get('campaign') or '—'}`.",f"- Measured awaiting canonical ingest: **{len(p['pending_canonical_ingest'])}**.",f"- Frozen and still unmeasured: **{len(p['frozen_unmeasured'])}**.",f"- Failed frozen forward gates: **{p['failed_forward_count']}**.",f"- Current bottleneck: **{p['bottleneck']['stage']}** — {p['bottleneck']['reason']}","","## Belief updates",""]
    for row in payload["belief_updates"]:
        lines.append(f"- **{row['id']} · {row['state']}** — {row['evidence']} _{row['uncertainty']}_")
    lines += ["","## Research-budget route",""]
    if r["next_action"]:
        action=r["next_action"]; campaign=f" `{action.get('campaign')}`" if action.get("campaign") else ""
        lines.append(f"**Next:** `{action.get('action')}`{campaign} — {action.get('why')}")
    else:
        lines.append("**Next:** no deterministic pipeline action is currently encoded.")
    if r["current_state_backlog"]:
        lines.append("")
        lines.append("Current-state backlog (recompute after the next evidence transition):")
        for action in r["current_state_backlog"]:
            campaign=f" `{action.get('campaign')}`" if action.get("campaign") else ""
            lines.append(f"- `{action.get('action')}`{campaign} — {action.get('why')}")
    else:
        lines.append("")
        lines.append("Current-state backlog: none. Recompute after the next evidence transition.")
    budget=r["new_hypothesis_budget"]
    lines += ["",f"New-hypothesis budget: **{budget['state']}** — {budget['why']}","",f"Mutation guardrail: **{r['mutation_guardrail']}**",""]
    return "\n".join(lines)

def render():
    payload=build_payload(); return payload, build_markdown(payload)

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--check", action="store_true"); args=parser.parse_args()
    payload, markdown=render(); text=json.dumps(payload, indent=2, sort_keys=True, allow_nan=False)+"\n"
    if args.check:
        if not OUT_JSON.exists() or json.loads(OUT_JSON.read_text()) != payload: raise SystemExit("docs/data/learning_router.json is stale")
        if not OUT_MD.exists() or OUT_MD.read_text() != markdown: raise SystemExit("docs/LEARNING_ROUTER.md is stale")
        print("learning router is current"); return
    OUT_JSON.write_text(text); OUT_MD.write_text(markdown); print(OUT_JSON); print(OUT_MD)

if __name__=="__main__": main()
