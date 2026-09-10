"""Finite preregistered iteration, exact benchmarks, resume and stack ranking.

No auto-promotion and no continuous scheduling. Each invocation has a budget.
Local Quantiacs market-data research uses the toolbox's public/default access
sentinel when no participant credential is configured.
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
from research.benchmark import (ROOT, QuantiacsEvaluator, check_causality, control_weights,
    digest, load_module, panel_hash, policy, residual_diagnostics, selection_score, validate_panel)


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


def rank_rows(records):
    rows = []
    for r in records:
        row = {k: r[k] for k in ("id", "family", "mode", "status")}
        row.update(rank=None, selection_score=None, worst_drawdown=None, mean_turnover=None)
        if r["status"] == "COMPLETE":
            row["selection_score"] = selection_score(r["metrics"])
            cells = [r["metrics"][fold][cost] for fold in ("research", "dev") for cost in ("0.04", "0.08", "0.12")]
            dd = [v["max_drawdown"] for v in cells]
            turnover = [v["avg_turnover"] for v in cells]
            if all(v is not None and np.isfinite(v) for v in dd + turnover):
                row["worst_drawdown"] = min(dd)
                row["mean_turnover"] = float(np.mean(turnover))
            else:
                row["selection_score"] = None
        rows.append(row)
    eligible = [r for r in rows if r["selection_score"] is not None]
    eligible.sort(key=lambda r: (-r["selection_score"], -r["worst_drawdown"], r["mean_turnover"], r["id"]))
    for i, row in enumerate(eligible, 1):
        row["rank"] = i
    return eligible + sorted([r for r in rows if r["selection_score"] is None], key=lambda r: r["id"])


def family_decisions(manifest, records):
    by_id = {r["id"]: r for r in records}
    decisions = []
    for family in sorted({c["family"] for c in manifest["candidates"]}):
        candidates = [c for c in manifest["candidates"] if c["family"] == family]
        rows = [by_id.get(c["id"]) for c in candidates]
        result = dict(family=family, decision="PENDING", family_rank=None, median_score=None,
                      reason="all preregistered variants and destructive controls required")
        if all(r and r["status"] == "COMPLETE" for r in rows):
            scores = {r["id"]: selection_score(r["metrics"]) for r in rows}
            if all(v is not None for v in scores.values()):
                bases = [c for c in candidates if c["mode"] == "base"]
                base_scores = [scores[c["id"]] for c in bases]
                controls = [c for c in candidates if c["mode"] != "base"]
                fails = [c["id"] for c in controls if scores[c["id"]] >= scores[c["parent_id"]]]
                result.update(median_score=float(np.median(base_scores)), plateau_min=min(base_scores),
                    decision="FREEZE" if fails else "NEEDS_FORWARD_EVIDENCE",
                    reason="destructive control/ablation matches or beats parent" if fails else "development evidence only; validation and policy gates pending",
                    failed_controls=fails)
        if any(r and r["status"] == "FAILED" for r in rows):
            result.update(decision="FREEZE", reason="execution or integrity failure; inspect ledger")
        decisions.append(result)
    scored = sorted([r for r in decisions if r["median_score"] is not None], key=lambda r: (-r["median_score"], r["family"]))
    for i, r in enumerate(scored, 1):
        r["family_rank"] = i
    return decisions


def report(directory, manifest, records, context):
    rankings = rank_rows(records)
    families = family_decisions(manifest, records)
    write_json(directory / "rankings.json", dict(context=context, candidates=rankings, families=families))
    lines = ["# Frontier benchmark", "", "Development research ranking, not contest qualification or a live forecast.", "",
             "| Rank | Candidate | Mode | Worst fold/cost Sharpe | Status |", "|---:|---|---|---:|---|"]
    for r in rankings:
        lines.append(f"| {r['rank'] or '—'} | {r['id']} | {r['mode']} | {r['selection_score'] if r['selection_score'] is not None else 'PENDING'} | {r['status']} |")
    lines += ["", f"Quantiacs local access mode: {context.get('quantiacs_access_mode', 'unknown')}.",
              "Public/default access is sufficient for local market-data research; it is not account-bound uniqueness clearance.", "",
              "Family ranking uses median development robustness score across the entire declared grid.",
              "A ranked family may be frozen by its falsifier. Rank is not permission to promote.", "",
              "| Family rank | Family | Decision | Reason |", "|---:|---|---|---|"]
    for f in families:
        lines.append(f"| {f['family_rank'] or '—'} | {f['family']} | {f['decision']} | {f['reason']} |")
    lines += ["", "Validation, diagnostic, full IS eligibility, hosted multipass and uniqueness: PENDING.",
              "Existing policy soft thresholds remain unset; automatic promotion is disabled.",
              "Historical roster metrics are not attached to current code or mixed into this ranking."]
    (directory / "report.md").write_text("\n".join(lines) + "\n")
    write_json(directory / "freeze_ledger.json", families)


def run(manifest_path, output, budget=18):
    if budget < 1:
        raise ValueError("budget must be positive")
    manifest = load_manifest(manifest_path)
    folds, costs = policy()
    output.mkdir(parents=True, exist_ok=True)
    access_mode = "unknown"
    # Failed setup gets a reviewable record instead of fictitious performance.
    try:
        ensure_local_data_access()
        access_mode = quantiacs_access_mode()
        # qnt reads API_KEY during import, so access must be configured first.
        import qnt.data as qndata
        import qnt.stats as qnstats
        data = qndata.cryptodaily_load_data(min_date="2015-01-01", max_date=folds[-1]["end"])
        data = data.sel(time=slice("2015-01-01", folds[-1]["end"]))
        validate_panel(data, folds[0]["start"], folds[-1]["end"])
    except (Exception, SystemExit) as e:
        blocked = output / ("blocked_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
        blocked.mkdir()
        # Exception messages from network libraries can contain request secrets.
        reason = type(e).__name__ + ": toolbox/data setup failed"
        write_json(blocked / "status.json", dict(status="BLOCKED", reason=reason, metrics=None,
                                                   quantiacs_access_mode=access_mode))
        records = [dict(id=c["id"], family=c["family"], mode=c["mode"], status="PENDING") for c in manifest["candidates"]]
        report(blocked, manifest, records, dict(status="BLOCKED", reason=reason,
                                                quantiacs_access_mode=access_mode))
        return blocked, False
    source_hashes = {c["path"]: sha256_file(ROOT / c["path"]) for c in manifest["candidates"]}
    for name in ("research/benchmark.py", "research/iteration.py", "configs/promotion_gates.yaml"):
        source_hashes[name] = sha256_file(ROOT / name)
    context = dict(manifest_sha256=sha256_file(manifest_path), data_sha256=panel_hash(data),
                   source_hashes=source_hashes, folds=folds, costs=costs,
                   toolbox_stats_sha256=sha256_file(qnstats.__file__), python=platform.python_version(),
                   numpy=np.__version__, pandas=pd.__version__, status="DEVELOPMENT_ONLY",
                   quantiacs_access_mode=access_mode)
    directory = output / digest(context)[:20]
    directory.mkdir(exist_ok=True)
    write_json(directory / "context.json", context)
    evaluator = QuantiacsEvaluator(data)
    jobs = [dict(id=name, family="control", mode="control", params={}) for name in manifest["controls"]] + manifest["candidates"]
    count = 0
    for c in jobs:
        path = directory / (c["id"] + ".json")
        if path.exists():
            continue  # failures are preserved; no invisible retries
        if count >= budget:
            break
        count += 1
        append(directory / "attempts.jsonl", dict(id=c["id"], started_utc=datetime.now(timezone.utc).isoformat()))
        started = time.perf_counter()
        record = dict(id=c["id"], family=c["family"], mode=c["mode"], params=c["params"], status="FAILED", metrics={})
        try:
            if c["mode"] == "control":
                fn = lambda d, name=c["id"]: control_weights(d, name)
            else:
                module = load_module(ROOT / c["path"])
                fn = lambda d, m=module, candidate=c: m.strategy(d, candidate["params"], candidate["mode"])
            weights = fn(data)
            record["causality"] = check_causality(fn, data, weights)
            metrics, returns = evaluator.evaluate(weights, folds, costs)
            record.update(status="COMPLETE", metrics=metrics)
            pd.concat(returns, axis=1).to_csv(directory / (c["id"] + "_returns.csv"))
        except Exception as e:
            record["failure"] = type(e).__name__ + ": evaluation or integrity check failed"
        record["runtime_seconds"] = time.perf_counter() - started
        write_json(path, record)
        Registry(directory / "registry.jsonl").append(RunRecord(run_id=directory.name + "_" + c["id"],
            idea_id=c["id"], strategy_path=c.get("path", "research/benchmark.py"), params=c["params"],
            family=c["family"], metrics=record["metrics"], status="ran" if record["status"] == "COMPLETE" else "failed",
            notes=f"Development folds only; hard/soft qualification pending; access={access_mode}"))
        print(c["id"], record["status"], flush=True)
    records = []
    streams = {}
    for c in jobs:
        path = directory / (c["id"] + ".json")
        records.append(json.loads(path.read_text()) if path.exists() else dict(id=c["id"], family=c["family"], mode=c["mode"], status="PENDING"))
        rr = directory / (c["id"] + "_returns.csv")
        if rr.exists():
            frame = pd.read_csv(rr, index_col=0, parse_dates=True)
            streams[c["id"]] = {f: frame[f].dropna() for f in ("research", "dev")}
    controls = {k: streams[k] for k in manifest["controls"] if k in streams}
    diagnostics = {}
    if len(controls) == len(manifest["controls"]):
        diagnostics = {k: residual_diagnostics(v, controls) for k, v in streams.items() if k not in controls}
    write_json(directory / "residual_diagnostics.json", diagnostics)
    report(directory, manifest, records, context)
    return directory, all(r["status"] == "COMPLETE" for r in records)


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
