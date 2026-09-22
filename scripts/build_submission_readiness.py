#!/usr/bin/env python3
"""Build evidence-backed Q25 submission-readiness telemetry.

This surface does not rank strategies. It separates exact artifact packaging,
full-history economics, frozen forward confidence, public/default correlation
smoke, and participant/account-bound uniqueness clearance.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "docs" / "data" / "submission_readiness.json"
OUT_MD = ROOT / "docs" / "SUBMISSION_READINESS.md"
PUBLIC = ROOT / "evidence" / "submission_readiness" / "public_correlation_smoke.json"

CANDIDATES = (
    {
        "id": "ebenezar_20260912_sharpe7_vol2",
        "label": "Sharpe7 Vol2",
        "artifact": "submissions/q25_sharpe7_vol2_multipass.py",
        "receipt": "evidence/deadline_20260918_sharpe7/hardening_receipt.json",
        "public_key": "sharpe7",
        "forward": "evidence/submission_readiness/sharpe7_forward_validation.json",
    },
    {
        "id": "q25_sota_meta_ensemble_v1",
        "label": "SOTA Meta",
        "artifact": "submissions/q25_sota_meta_ensemble_multipass.py",
        "receipt": "evidence/deadline_20260918_sota_meta/measurement_receipt.json",
        "public_key": "sota",
        "forward": None,
    },
    {
        "id": "ebenezar_20260912_lattice_consensus",
        "label": "Lattice Consensus",
        "artifact": "submissions/q25_lattice_consensus_multipass.py",
        "receipt": "evidence/deadline_20260918_lattice_consensus/hardening_receipt.json",
        "public_key": "lattice",
        "forward": None,
    },
)


def load(path: Path, default: Any = None) -> Any:
    return json.loads(path.read_text()) if path.exists() else default


def f(value: Any) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def pass_floor(value: float | None) -> bool | None:
    return None if value is None else value > 1.0


def full_history(receipt: dict[str, Any]) -> dict[str, Any]:
    if "authoritative_full_history_measurement" in receipt:
        m = receipt["authoritative_full_history_measurement"]
        sr4 = f((m.get("cost_0_04") or {}).get("sharpe_ratio"))
        sr12 = f((m.get("cost_0_12") or {}).get("sharpe_ratio"))
        rep = receipt.get("hardening_replication") or {}
        sr10 = f(((rep.get("cost_ladder") or {}).get("0.10") or {}).get("sharpe_ratio"))
        run_id = m.get("workflow_run_id")
    else:
        m = receipt.get("authoritative_full_history_multipass") or {}
        sr4 = f(m.get("cost_0_04_sharpe"))
        sr10 = f(m.get("cost_0_10_sharpe"))
        sr12 = f(m.get("cost_0_12_sharpe"))
        run_id = m.get("workflow_run_id")
    return {
        "workflow_run_id": run_id,
        "sharpe_4pct_atr": sr4,
        "sharpe_10pct_atr": sr10,
        "sharpe_12pct_atr": sr12,
        "contest_floor_4pct_pass": pass_floor(sr4),
        "stress_10pct_pass": pass_floor(sr10),
        "stress_12pct_pass": pass_floor(sr12),
    }


def forward(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {
            "state": "NOT_MEASURED",
            "validation_window": None,
            "sharpe_4pct_atr": None,
            "sharpe_10pct_atr": None,
            "pass_4pct": None,
            "pass_10pct": None,
            "source_path": None,
        }
    r = load(path, {})
    v = r.get("validation_2023_2024") or {}
    sr4 = f((v.get("0.04") or {}).get("sharpe_ratio"))
    sr10 = f((v.get("0.10") or {}).get("sharpe_ratio"))
    return {
        "state": "FROZEN_FORWARD_OBSERVED",
        "validation_window": r.get("validation_window"),
        "sharpe_4pct_atr": sr4,
        "sharpe_10pct_atr": sr10,
        "pass_4pct": pass_floor(sr4),
        "pass_10pct": pass_floor(sr10),
        "source_path": str(path.relative_to(ROOT)),
        "workflow_run_id": r.get("workflow_run_id"),
        "artifact_id": r.get("artifact_id"),
        "artifact_sha256": r.get("artifact_sha256"),
        "protected_live_start": r.get("protected_live_start"),
        "last_market_date": r.get("last_market_date"),
        "post_validation_diagnostic": r.get("diagnostic_2025_to_2026_09_17"),
        "last_365_days_at_0_04": r.get("last_365_days_at_0_04"),
    }


def public_smoke(public: dict[str, Any], key: str) -> dict[str, Any]:
    row = (public.get("candidates") or {}).get(key)
    if not row:
        return {"state": "NOT_RUN", "participant_id": None, "account_bound_clearance": False}
    participant_id = str(row.get("participant_id", "0"))
    return {
        "state": row.get("state"),
        "message": row.get("message"),
        "participant_id": participant_id,
        "workflow_run_id": public.get("workflow_run_id"),
        "artifact_id": row.get("artifact_id"),
        "artifact_sha256": row.get("artifact_sha256"),
        "account_bound_clearance": participant_id not in {"", "0", "None", "null"},
        "scope_note": public.get("scope_note"),
    }


def stage(packaged: bool, full: dict[str, Any], fw: dict[str, Any], smoke: dict[str, Any]) -> str:
    if not packaged:
        return "QUALIFIED_SOURCE_NOT_PACKAGED" if full["contest_floor_4pct_pass"] else "NOT_SUBMISSION_READY"
    if full["contest_floor_4pct_pass"] is not True:
        return "PACKAGED_BUT_ECONOMIC_GATE_NOT_CLEARED"
    if smoke.get("account_bound_clearance"):
        return "ACCOUNT_BOUND_CLEAR"
    if fw["state"] == "FROZEN_FORWARD_OBSERVED":
        if fw["pass_4pct"] and fw["pass_10pct"] is not False:
            return "PROMOTED_FORWARD_PASS_PENDING_ACCOUNT_BOUND_CORRELATION"
        return "PROMOTED_FORWARD_WEAK_PENDING_ACCOUNT_BOUND_CORRELATION"
    return "PROMOTED_PENDING_FORWARD_AND_ACCOUNT_BOUND_CORRELATION"


def build_payload() -> dict[str, Any]:
    public = load(PUBLIC, {})
    rows = []
    for cfg in CANDIDATES:
        receipt = load(ROOT / cfg["receipt"])
        if not receipt:
            continue
        full = full_history(receipt)
        fw_path = ROOT / cfg["forward"] if cfg["forward"] else None
        fw = forward(fw_path)
        smoke = public_smoke(public, cfg["public_key"])
        packaged = (ROOT / cfg["artifact"]).exists()
        blockers = []
        if not packaged:
            blockers.append("PACKAGE_EXACT_MULTIPASS_ARTIFACT")
        if full["contest_floor_4pct_pass"] is not True:
            blockers.append("FULL_HISTORY_4PCT_SHARPE_FLOOR")
        if packaged and fw["state"] == "NOT_MEASURED":
            blockers.append("FROZEN_FORWARD_CONFIDENCE_NOT_MEASURED")
        elif fw["state"] == "FROZEN_FORWARD_OBSERVED" and fw["pass_4pct"] is False:
            blockers.append("FROZEN_FORWARD_4PCT_FAILED")
        if packaged and not smoke.get("account_bound_clearance"):
            blockers.append("ACCOUNT_BOUND_UNIQUENESS_CORRELATION")
        rows.append({
            "id": cfg["id"],
            "label": cfg["label"],
            "production_artifact": cfg["artifact"],
            "artifact_present": packaged,
            "source_blob_sha": receipt.get("source_blob_sha"),
            "stage": stage(packaged, full, fw, smoke),
            "full_history": full,
            "forward_validation": fw,
            "public_correlation_smoke": smoke,
            "blockers": blockers,
            "receipt_path": cfg["receipt"],
        })

    return {
        "schema_version": 1,
        "policy": {
            "strategy_ranking": "FORBIDDEN_ON_THIS_SURFACE",
            "missing_evidence": "stays missing",
            "public_smoke_is_account_clearance": False,
            "forward_evidence_changes_confidence_not_formula": True,
            "purpose": "submission operational readiness for exact frozen artifacts",
        },
        "summary": {
            "candidate_count": len(rows),
            "packaged_count": sum(row["artifact_present"] for row in rows),
            "full_history_floor_pass_count": sum(row["full_history"]["contest_floor_4pct_pass"] is True for row in rows),
            "frozen_forward_observed_count": sum(row["forward_validation"]["state"] == "FROZEN_FORWARD_OBSERVED" for row in rows),
            "public_smoke_clear_count": sum(row["public_correlation_smoke"].get("state") == "PUBLIC_DEFAULT_CLEAR" for row in rows),
            "account_bound_clear_count": sum(row["public_correlation_smoke"].get("account_bound_clearance") is True for row in rows),
        },
        "candidates": rows,
        "hard_blocker": "Participant/account-bound uniqueness correlation must be run on the exact final artifact before treating public smoke as contest clearance.",
    }


def fmt(value: Any, digits: int = 3) -> str:
    return "—" if value is None else (f"{value:.{digits}f}" if isinstance(value, float) else str(value))


def build_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    lines = [
        "---",
        "title: Submission Readiness",
        "description: Evidence-backed operational readiness of exact frozen Q25 submission artifacts.",
        "---",
        "",
        "# Q25 submission readiness",
        "",
        "> This is not a strategy ranking. It separates packaging, full-history economics, frozen forward confidence, public/default correlation smoke, and participant/account-bound uniqueness clearance.",
        "",
        f"Packaged artifacts: **{s['packaged_count']}/{s['candidate_count']}** · full-history 4%-ATR floor pass: **{s['full_history_floor_pass_count']}/{s['candidate_count']}** · frozen forward observed: **{s['frozen_forward_observed_count']}** · public smoke clear: **{s['public_smoke_clear_count']}** · account-bound clear: **{s['account_bound_clear_count']}**.",
        "",
        "| Candidate | Stage | Artifact | Full SR @4% | SR @10% | SR @12% | Frozen forward @4% | Public smoke | Remaining blockers |",
        "|---|---|---|---:|---:|---:|---:|---|---|",
    ]
    for row in payload["candidates"]:
        m, fw, p = row["full_history"], row["forward_validation"], row["public_correlation_smoke"]
        blockers = ", ".join(row["blockers"]) if row["blockers"] else "none"
        lines.append(
            f"| **{row['label']}** | `{row['stage']}` | {'yes' if row['artifact_present'] else 'no'} | "
            f"{fmt(m['sharpe_4pct_atr'])} | {fmt(m['sharpe_10pct_atr'])} | {fmt(m['sharpe_12pct_atr'])} | "
            f"{fmt(fw['sharpe_4pct_atr'])} | `{p.get('state') or 'NOT_RUN'}` | {blockers} |"
        )
    lines += [
        "",
        "## Hard boundary",
        "",
        payload["hard_blocker"],
        "",
        "A clean public/default correlation response with `PARTICIPANT_ID=0` is useful smoke evidence, but it is **not** account-bound uniqueness clearance.",
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
            raise SystemExit("docs/data/submission_readiness.json is stale")
        if not OUT_MD.exists() or OUT_MD.read_text() != markdown:
            raise SystemExit("docs/SUBMISSION_READINESS.md is stale")
        print("submission readiness is current")
        return
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(text)
    OUT_MD.write_text(markdown)
    print(OUT_JSON)
    print(OUT_MD)


if __name__ == "__main__":
    main()
