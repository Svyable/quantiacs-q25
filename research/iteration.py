"""Finite preregistered iteration, exact benchmarks, resumable evidence packets.

A cell failure is not a mechanism failure. Independent preregistered cells continue
running; family decisions are made after the evidence packet exists.
"""
from __future__ import annotations
import argparse
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
from factory.registry import Registry, RunRecord
from factory.runner import ensure_local_data_access, quantiacs_access_mode
from research.preregister import sha256_file
from research.campaign import CAMPAIGN
from research.benchmark import (
    ROOT, QuantiacsEvaluator, check_causality, control_weights, digest, load_module,
    panel_hash, policy, residual_diagnostics, selection_score, validate_panel,
)

SCHEMA_VERSION = 2
COMPLETE = "COMPLETE"
FAILURE_STATUSES = {"FAILED_SOFTWARE", "FAILED_INTEGRITY", "FAILED_SOURCE_AUDIT"}
DEVELOPMENT_FLOOR = 1.0


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def append(path, value):
    with path.open("a") as f:
        f.write(json.dumps(value, sort_keys=True, allow_nan=False) + "\n")


def load_manifest(path):
    manifest = json.loads(path.read_text())
    ids = [c["id"] for c in manifest["candidates"]]
    if len(ids) != len(set(ids)) or len(ids) > manifest["max_unique_candidates"]:
        raise ValueError("duplicate ids or exceeded preregistered budget")
    for c in manifest["candidates"]:
        prereg = ROOT / c["preregistration"]
        if sha256_file(prereg) != c["preregistration_sha256"]:
            raise ValueError("preregistration changed: " + c["id"])
        spec = json.loads(prereg.read_text())
        expected = dict(spec["params"], window=c["params"]["window"])
        if c["params"] != expected or c["params"]["window"] not in spec["grid"]["window"]:
            raise ValueError("candidate outside preregistered grid")
        if c["path"] != spec["code_path"] or c["mode"] not in {"base", "falsifier", "ablation"}:
            raise ValueError("candidate contract mismatch")
        source = (ROOT / c["path"]).read_text()
        if c["preregistration_sha256"] not in source:
            raise ValueError("source missing preregistration hash")
    return manifest


def failure_status(stage):
    if stage == "source_audit":
        return "FAILED_SOURCE_AUDIT"
    if stage in {"causality", "evaluation"}:
        return "FAILED_INTEGRITY"
    return "FAILED_SOFTWARE"


def metric_packet(record):
    packet = {
        "schema_version": SCHEMA_VERSION,
        "id": record["id"],
        "family": record["family"],
        "mode": record["mode"],
        "status": record["status"],
        "rankable": False,
        "selection_score": None,
        "research_sharpe_0": None,
        "research_sharpe_12": None,
        "dev_sharpe_0": None,
        "dev_sharpe_12": None,
        "worst_drawdown_12": None,
        "mean_turnover_12": None,
        "evidence_completeness": 0.0,
    }
    if record["status"] != COMPLETE:
        packet["failure_stage"] = record.get("failure_stage")
        packet["failure_type"] = record.get("failure_type")
        return packet
    m = record["metrics"]
    packet["selection_score"] = selection_score(m)
    packet["research_sharpe_0"] = m["research"]["0.00"]["sharpe_ratio"]
    packet["research_sharpe_12"] = m["research"]["0.12"]["sharpe_ratio"]
    packet["dev_sharpe_0"] = m["dev"]["0.00"]["sharpe_ratio"]
    packet["dev_sharpe_12"] = m["dev"]["0.12"]["sharpe_ratio"]
    dds = [m[f]["0.12"]["max_drawdown"] for f in ("research", "dev")]
    turns = [m[f]["0.12"]["avg_turnover"] for f in ("research", "dev")]
    packet["worst_drawdown_12"] = min(dds) if all(v is not None and np.isfinite(v) for v in dds) else None
    packet["mean_turnover_12"] = float(np.mean(turns)) if all(v is not None and np.isfinite(v) for v in turns) else None
    required = [
        packet["selection_score"], packet["research_sharpe_0"], packet["research_sharpe_12"],
        packet["dev_sharpe_0"], packet["dev_sharpe_12"], packet["worst_drawdown_12"],
        packet["mean_turnover_12"],
    ]
    packet["evidence_completeness"] = sum(v is not None and np.isfinite(v) for v in required) / len(required)
    packet["rankable"] = packet["evidence_completeness"] == 1.0
    return packet


def rank_rows(records):
    rows = [metric_packet(r) for r in records]
    eligible = [r for r in rows if r["rankable"]]
    eligible.sort(key=lambda r: (-r["selection_score"], -r["worst_drawdown_12"], r["mean_turnover_12"], r["id"]))
    for i, row in enumerate(eligible, 1):
        row["rank"] = i
    for row in rows:
        row.setdefault("rank", None)
    return eligible + sorted([r for r in rows if not r["rankable"]], key=lambda r: r["id"])


def family_decisions(manifest, records):
    by_id = {r["id"]: r for r in records}
    decisions = []
    families = sorted({c["family"] for c in manifest["candidates"]})
    for family in families:
        candidates = [c for c in manifest["candidates"] if c["family"] == family]
        present = [by_id[c["id"]] for c in candidates if c["id"] in by_id]
        complete = [r for r in present if r.get("status") == COMPLETE]
        invalid = [r for r in present if r.get("status") in FAILURE_STATUSES or r.get("status") == "FAILED"]
        pending_ids = [c["id"] for c in candidates if c["id"] not in by_id or by_id[c["id"]].get("status") == "PENDING"]
        bases = [c for c in candidates if c["mode"] == "base"]
        complete_bases = [by_id[c["id"]] for c in bases if by_id.get(c["id"], {}).get("status") == COMPLETE]
        base_scores = [selection_score(r["metrics"]) for r in complete_bases]
        base_scores = [v for v in base_scores if v is not None]
        controls = [c for c in candidates if c["mode"] != "base"]
        failed_controls = []
        for c in controls:
            child = by_id.get(c["id"])
            parent = by_id.get(c.get("parent_id"))
            if child and parent and child.get("status") == COMPLETE and parent.get("status") == COMPLETE:
                child_score = selection_score(child["metrics"])
                parent_score = selection_score(parent["metrics"])
                if child_score is not None and parent_score is not None and child_score >= parent_score:
                    failed_controls.append(c["id"])

        result = {
            "family": family,
            "decision": "PENDING",
            "decision_code": "INSUFFICIENT_VALID_EVIDENCE",
            "family_rank": None,
            "median_score": float(np.median(base_scores)) if base_scores else None,
            "best_score": max(base_scores) if base_scores else None,
            "completed_cells": len(complete),
            "declared_cells": len(candidates),
            "invalid_cells": [r["id"] for r in invalid],
            "pending_cells": pending_ids,
            "failed_controls": failed_controls,
            "reason": "no valid base cell",
        }
        if pending_ids:
            result.update(
                decision="PENDING",
                decision_code="PARTIAL_CAMPAIGN",
                reason="preregistered cells remain unattempted; do not family-rank a partial campaign",
            )
        elif failed_controls:
            result.update(
                decision="FREEZE",
                decision_code="FALSIFIED_DEVELOPMENT",
                reason="destructive control/ablation matches or beats its valid parent",
            )
        elif base_scores and max(base_scores) < DEVELOPMENT_FLOOR:
            result.update(
                decision="FREEZE",
                decision_code="KILL_WEAK_ALPHA",
                reason=f"every valid base cell is below predefined development floor Sharpe {DEVELOPMENT_FLOOR:.1f}",
            )
        elif base_scores and invalid:
            result.update(
                decision="CONTINUE",
                decision_code="REPAIR_INVALID_CELLS_THEN_FORWARD",
                reason="promising valid base evidence exists; invalid cells are implementation/integrity failures, not mechanism falsification",
            )
        elif base_scores:
            result.update(
                decision="CONTINUE",
                decision_code="NEEDS_FORWARD_EVIDENCE",
                reason="development evidence only; validation, policy, originality and account-bound gates remain pending",
            )
        decisions.append(result)

    scored = sorted(
        [r for r in decisions if r["median_score"] is not None and not r["pending_cells"]],
        key=lambda r: (-r["median_score"], r["family"]),
    )
    for i, row in enumerate(scored, 1):
        row["family_rank"] = i
    return decisions


def report(directory, manifest, records, context):
    rankings = rank_rows(records)
    families = family_decisions(manifest, records)
    matrix = {
        "schema_version": SCHEMA_VERSION,
        "context": context,
        "candidates": rankings,
        "families": families,
        "evidence_model": {
            "strategy_quality": "economic metrics from valid observed cells",
            "evidence_quality": "completeness/provenance; development is not validation",
            "implementation_health": "software/integrity state; never conflated with economic falsification",
        },
    }
    write_json(directory / "rankings.json", matrix)
    write_json(directory / "matrix.json", matrix)
    lines = [
        "# Frontier benchmark", "",
        "Development research ranking, not contest qualification or a live forecast.", "",
        "| Rank | Candidate | Mode | Worst fold/cost SR | Research SR @12% | Dev SR @12% | Worst DD @12% | Status |",
        "|---:|---|---|---:|---:|---:|---:|---|",
    ]
    for r in rankings:
        score = "—" if r["selection_score"] is None else f'{r["selection_score"]:.3f}'
        rs = "—" if r["research_sharpe_12"] is None else f'{r["research_sharpe_12"]:.3f}'
        ds = "—" if r["dev_sharpe_12"] is None else f'{r["dev_sharpe_12"]:.3f}'
        dd = "—" if r["worst_drawdown_12"] is None else f'{100*r["worst_drawdown_12"]:.1f}%'
        lines.append(f'| {r["rank"] or "—"} | {r["id"]} | {r["mode"]} | {score} | {rs} | {ds} | {dd} | {r["status"]} |')
    lines += [
        "", f"Quantiacs local access mode: {context.get('quantiacs_access_mode', 'unknown')}.",
        "Public/default access is sufficient for local market-data research; it is not account-bound uniqueness clearance.", "",
        "### Family adjudication", "",
        "| Family rank | Family | Best score | Valid cells | Action | Decision code | Reason |",
        "|---:|---|---:|---:|---|---|---|",
    ]
    for row in families:
        best = "—" if row["best_score"] is None else f'{row["best_score"]:.3f}'
        lines.append(f'| {row["family_rank"] or "—"} | {row["family"]} | {best} | {row["completed_cells"]}/{row["declared_cells"]} | {row["decision"]} | {row["decision_code"]} | {row["reason"]} |')
    lines += [
        "", "A failed implementation cell does **not** freeze an otherwise independent preregistered family.",
        "Falsification is economic: a valid destructive control matching/beating its valid parent, or a predefined weak-alpha floor.",
        "Validation, diagnostic, full-IS eligibility, hosted multipass and uniqueness remain PENDING.",
        "Historical roster metrics are not mixed into this development ranking.",
    ]
    (directory / "report.md").write_text("\n".join(lines) + "\n")
    write_json(directory / "freeze_ledger.json", families)


def run(manifest_path, output, budget=18):
    if budget < 1:
        raise ValueError("budget must be positive")
    manifest = load_manifest(manifest_path)
    folds, costs = policy()
    output.mkdir(parents=True, exist_ok=True)
    access_mode = "unknown"
    try:
        ensure_local_data_access()
        access_mode = quantiacs_access_mode()
        import qnt.data as qndata
        import qnt.stats as qnstats
        data = qndata.cryptodaily_load_data(min_date="2015-01-01", max_date=folds[-1]["end"])
        data = data.sel(time=slice("2015-01-01", folds[-1]["end"]))
        validate_panel(data, folds[0]["start"], folds[-1]["end"])
    except (Exception, SystemExit) as e:
        blocked = output / ("blocked_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
        blocked.mkdir()
        reason = type(e).__name__ + ": toolbox/data setup failed"
        write_json(blocked / "status.json", dict(status="BLOCKED_INFRA", reason=reason, metrics=None, quantiacs_access_mode=access_mode))
        records = [dict(id=c["id"], family=c["family"], mode=c["mode"], status="PENDING") for c in manifest["candidates"]]
        report(blocked, manifest, records, dict(status="BLOCKED_INFRA", reason=reason, quantiacs_access_mode=access_mode))
        return blocked, False

    source_hashes = {c["path"]: sha256_file(ROOT / c["path"]) for c in manifest["candidates"]}
    for name in ("research/benchmark.py", "research/iteration.py", "configs/promotion_gates.yaml"):
        source_hashes[name] = sha256_file(ROOT / name)
    context = dict(
        schema_version=SCHEMA_VERSION,
        manifest_sha256=sha256_file(manifest_path), data_sha256=panel_hash(data),
        source_hashes=source_hashes, folds=folds, costs=costs,
        toolbox_stats_sha256=sha256_file(qnstats.__file__), python=platform.python_version(),
        numpy=np.__version__, pandas=pd.__version__, status="DEVELOPMENT_ONLY",
        quantiacs_access_mode=access_mode,
    )
    directory = output / digest(context)[:20]
    directory.mkdir(exist_ok=True)
    write_json(directory / "context.json", context)
    evaluator = QuantiacsEvaluator(data)
    jobs = [dict(id=name, family="control", mode="control", params={}) for name in manifest["controls"]] + manifest["candidates"]
    count = 0
    for c in jobs:
        path = directory / (c["id"] + ".json")
        if path.exists():
            continue
        if count >= budget:
            break
        count += 1
        append(directory / "attempts.jsonl", dict(id=c["id"], started_utc=datetime.now(timezone.utc).isoformat()))
        started = time.perf_counter()
        record = dict(id=c["id"], family=c["family"], mode=c["mode"], params=c["params"], status="FAILED_SOFTWARE", metrics={})
        stage = "strategy"
        try:
            if c["mode"] == "control":
                fn = lambda d, name=c["id"]: control_weights(d, name)
            else:
                stage = "source_audit"
                module = load_module(ROOT / c["path"])
                fn = lambda d, m=module, candidate=c: m.strategy(d, candidate["params"], candidate["mode"])
            stage = "strategy"
            weights = fn(data)
            stage = "causality"
            record["causality"] = check_causality(fn, data, weights)
            stage = "evaluation"
            metrics, returns = evaluator.evaluate(weights, folds, costs)
            record.update(status=COMPLETE, metrics=metrics)
            pd.concat(returns, axis=1).to_csv(directory / (c["id"] + "_returns.csv"))
        except Exception as e:
            record["status"] = failure_status(stage)
            record["failure_stage"] = stage
            record["failure_type"] = type(e).__name__
            record["failure"] = f"{type(e).__name__}: {stage} check failed"
        record["runtime_seconds"] = time.perf_counter() - started
        write_json(path, record)
        packet_dir = directory / "candidate_packets"
        packet_dir.mkdir(exist_ok=True)
        write_json(packet_dir / (c["id"] + ".json"), metric_packet(record))
        Registry(directory / "registry.jsonl").append(RunRecord(
            run_id=directory.name + "_" + c["id"], idea_id=c["id"],
            strategy_path=c.get("path", "research/benchmark.py"), params=c["params"],
            family=c["family"], metrics=record["metrics"],
            status="ran" if record["status"] == COMPLETE else "failed",
            notes=f"Development folds only; hard/soft qualification pending; access={access_mode}; status={record['status']}",
        ))
        print(c["id"], record["status"], flush=True)

    records, streams = [], {}
    for c in jobs:
        path = directory / (c["id"] + ".json")
        records.append(json.loads(path.read_text()) if path.exists() else dict(id=c["id"], family=c["family"], mode=c["mode"], status="PENDING"))
        rr = directory / (c["id"] + "_returns.csv")
        if rr.exists():
            frame = pd.read_csv(rr, index_col=0, parse_dates=True)
            streams[c["id"]] = {f: frame[f].dropna() for f in ("research", "dev")}
    available_controls = {k: streams[k] for k in manifest["controls"] if k in streams}
    diagnostics = {"_meta": {
        "requested_controls": manifest["controls"],
        "available_controls": sorted(available_controls),
        "status": "COMPLETE" if len(available_controls) == len(manifest["controls"]) else "PARTIAL_CONTROLS",
    }}
    if available_controls:
        diagnostics.update({k: residual_diagnostics(v, available_controls) for k, v in streams.items() if k not in available_controls})
    write_json(directory / "residual_diagnostics.json", diagnostics)
    report(directory, manifest, records, context)
    attempted = [r for r in records if r["status"] != "PENDING"]
    return directory, bool(attempted)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", type=Path, default=ROOT / "experiments" / CAMPAIGN / "manifest.json")
    p.add_argument("--output", type=Path, default=ROOT / "results" / CAMPAIGN)
    p.add_argument("--budget", type=int, default=18, help="maximum previously unattempted candidates; rerun to resume")
    args = p.parse_args()
    path, complete = run(args.manifest, args.output, args.budget)
    print(path)
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
