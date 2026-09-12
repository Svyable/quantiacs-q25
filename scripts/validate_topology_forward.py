"""Frozen 2023-2024 forward validation for Frontier-B topology migration.

This script does not select or tune parameters. It evaluates the exact preregistered
family and original controls on the chronological validation fold only.
"""
from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd

from factory.runner import ensure_local_data_access, quantiacs_access_mode
from research.benchmark import (
    ROOT,
    QuantiacsEvaluator,
    check_causality,
    control_weights,
    load_module,
    panel_hash,
    validate_panel,
)
from research.preregister import sha256_file

PLAN_PATH = ROOT / "experiments/topology_forward_20260912/validation_plan.json"
OUTPUT_DIR = ROOT / "results/topology_forward_20260912"


def _write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def _finite_number(value):
    value = float(value) if value is not None else None
    return value if value is not None and np.isfinite(value) else None


def _report(results: dict) -> str:
    metrics = results["objects"]
    lines = [
        "# Topology migration — frozen 2023–2024 validation",
        "",
        "> This is the first chronological validation look for the already-selected Frontier-B topology-migration family. No parameter changes are permitted from this result.",
        "",
        f"**Forward gate: {results['forward_gate']['decision']}**",
        "",
        "| Object | Type | Validation SR @0% | SR @4% | SR @8% | SR @12% | CAGR @12% | Max DD @12% | Turnover @12% |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for object_id in results["order"]:
        row = metrics[object_id]
        m = row["metrics"]["validation"]
        def fmt(x):
            return "—" if x is None else f"{x:.3f}"
        lines.append(
            f"| `{object_id}` | {row['mode']} | {fmt(m['0.00']['sharpe_ratio'])} | {fmt(m['0.04']['sharpe_ratio'])} | "
            f"{fmt(m['0.08']['sharpe_ratio'])} | {fmt(m['0.12']['sharpe_ratio'])} | {fmt(m['0.12']['cagr'])} | "
            f"{fmt(m['0.12']['max_drawdown'])} | {fmt(m['0.12']['avg_turnover'])} |"
        )
    lines += [
        "",
        "## Frozen gate",
        "",
    ]
    for check in results["forward_gate"]["checks"]:
        lines.append(f"- **{'PASS' if check['passed'] else 'FAIL'}** — {check['name']}: {check['detail']}")
    lines += [
        "",
        "## Validation-only correlations at 4% ATR cost",
        "",
        "The selected `topology_migration_w84` return stream is compared with the three generic controls only as a validation diagnostic; no regression or new selection is fit on this fold.",
        "",
    ]
    for name, value in results["selected_validation_correlations"].items():
        lines.append(f"- `{name}`: {value:.3f}" if value is not None else f"- `{name}`: —")
    lines += [
        "",
        "## Evidence boundary",
        "",
        "A passing forward gate is stronger evidence than development performance, but it is **not** Q25 submission clearance. Full-IS eligibility, exact production parity, hosted multi-pass behavior, and participant-specific uniqueness/correlation remain separate gates. A failure here cannot be repaired by retuning on 2023–2024 or by opening 2025+ data.",
        "",
        "These are historical simulations, not forecasts or guarantees.",
    ]
    return "\n".join(lines) + "\n"


def run(output_dir: Path = OUTPUT_DIR) -> dict:
    plan = json.loads(PLAN_PATH.read_text())
    prereg = ROOT / plan["source_preregistration"]
    source = ROOT / plan["source_strategy"]
    if sha256_file(prereg) != plan["source_preregistration_sha256"]:
        raise RuntimeError("source preregistration hash changed before validation")
    if plan["source_preregistration_sha256"] not in source.read_text():
        raise RuntimeError("strategy source no longer declares the frozen preregistration hash")

    ensure_local_data_access()
    import qnt.data as qndata
    import qnt.stats as qnstats

    fold = {"id": "validation", **plan["validation_fold"]}
    data = qndata.cryptodaily_load_data(min_date="2015-01-01", max_date=fold["end"])
    data = data.sel(time=slice("2015-01-01", fold["end"]))
    validate_panel(data, fold["start"], fold["end"])
    evaluator = QuantiacsEvaluator(data)
    module = load_module(source)

    jobs = list(plan["objects"]) + [
        {"id": name, "mode": "control", "params": {}}
        for name in plan["generic_controls"]
    ]
    results = {}
    validation_returns = {}
    for job in jobs:
        if job["mode"] == "control":
            fn = lambda d, name=job["id"]: control_weights(d, name)
        else:
            fn = lambda d, j=job: module.strategy(d, j["params"], j["mode"])
        weights = fn(data)
        causality = check_causality(fn, data, weights)
        metrics, returns = evaluator.evaluate(weights, [fold], plan["cost_ladder"])
        validation_returns[job["id"]] = returns["validation"]
        results[job["id"]] = {
            "mode": job["mode"],
            "params": job["params"],
            "causality": causality,
            "metrics": metrics,
        }
        print(job["id"], metrics["validation"]["0.12"]["sharpe_ratio"], flush=True)

    focal = results[plan["selected_candidate_before_validation"]]["metrics"]["validation"]
    canonical = results["topology_migration_w63"]["metrics"]["validation"]
    ablation = results["topology_migration_ablation"]["metrics"]["validation"]
    falsifier = results["topology_migration_falsifier"]["metrics"]["validation"]
    base_ids = ["topology_migration_w42", "topology_migration_w63", "topology_migration_w84"]
    base_sr12 = {
        name: results[name]["metrics"]["validation"]["0.12"]["sharpe_ratio"]
        for name in base_ids
    }

    checks = [
        {
            "name": "selected_w84_sharpe_12_min",
            "passed": focal["0.12"]["sharpe_ratio"] is not None and focal["0.12"]["sharpe_ratio"] >= plan["forward_gate"]["selected_w84_sharpe_12_min"],
            "detail": f"w84 SR@12={focal['0.12']['sharpe_ratio']:.3f}; required >= {plan['forward_gate']['selected_w84_sharpe_12_min']:.3f}",
        },
        {
            "name": "selected_w84_all_cost_sharpes_positive",
            "passed": all(focal[f"{cost:.2f}"]["sharpe_ratio"] is not None and focal[f"{cost:.2f}"]["sharpe_ratio"] > 0 for cost in plan["cost_ladder"]),
            "detail": "all frozen cost-rung Sharpes must be positive",
        },
        {
            "name": "canonical_w63_beats_original_controls_at_12",
            "passed": canonical["0.12"]["sharpe_ratio"] > ablation["0.12"]["sharpe_ratio"] and canonical["0.12"]["sharpe_ratio"] > falsifier["0.12"]["sharpe_ratio"],
            "detail": f"w63={canonical['0.12']['sharpe_ratio']:.3f}, ablation={ablation['0.12']['sharpe_ratio']:.3f}, falsifier={falsifier['0.12']['sharpe_ratio']:.3f}",
        },
        {
            "name": "minimum_positive_base_windows_at_12",
            "passed": sum(value is not None and value > 0 for value in base_sr12.values()) >= plan["forward_gate"]["minimum_positive_base_windows_at_12"],
            "detail": f"positive base windows={sum(value is not None and value > 0 for value in base_sr12.values())}/3; required >= {plan['forward_gate']['minimum_positive_base_windows_at_12']}",
        },
    ]
    gate_decision = "PASS_FORWARD_STRONG" if all(c["passed"] for c in checks) else "FAIL_FORWARD_GATE"

    frame = pd.concat(validation_returns, axis=1)
    selected = plan["selected_candidate_before_validation"]
    correlations = {}
    for control in plan["generic_controls"]:
        pair = frame[[selected, control]].dropna()
        value = pair[selected].corr(pair[control]) if len(pair) else np.nan
        correlations[control] = _finite_number(value)

    context = {
        "status": "VALIDATION_ONLY",
        "quantiacs_access_mode": quantiacs_access_mode(),
        "validation_fold": fold,
        "cost_ladder": plan["cost_ladder"],
        "data_sha256": panel_hash(data),
        "plan_sha256": sha256_file(PLAN_PATH),
        "preregistration_sha256": sha256_file(prereg),
        "strategy_sha256": sha256_file(source),
        "benchmark_sha256": sha256_file(ROOT / "research/benchmark.py"),
        "toolbox_stats_sha256": sha256_file(qnstats.__file__),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
    }
    packet = {
        "context": context,
        "order": [job["id"] for job in jobs],
        "objects": results,
        "forward_gate": {"decision": gate_decision, "checks": checks},
        "selected_validation_correlations": correlations,
        "prohibitions": plan["prohibitions"],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "validation_results.json", packet)
    (output_dir / "validation_report.md").write_text(_report(packet))
    frame.to_csv(output_dir / "validation_returns_4pct.csv")
    print(gate_decision, flush=True)
    return packet


if __name__ == "__main__":
    run()
