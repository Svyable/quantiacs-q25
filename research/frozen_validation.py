"""Frozen chronological validation for a pre-selected Q25 strategy.

This module deliberately has no selection loop. It verifies the committed validation
plan and frozen source fingerprint before opening 2023-2024, evaluates exactly one
pre-selected implementation, and reports generic controls only as context.
"""
from __future__ import annotations

import argparse
import json
import platform
from datetime import datetime, timezone
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

DEFAULT_PLAN = ROOT / "experiments/frontier_20260910b/topology_migration/validation_plan.json"


def _write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def load_plan(path: Path = DEFAULT_PLAN) -> dict:
    plan = json.loads(path.read_text())
    if plan.get("status") != "FROZEN_PLAN_BEFORE_VALIDATION_OPEN":
        raise ValueError("validation plan is not frozen")
    if plan.get("decision_policy", {}).get("automatic_promotion") is not False:
        raise ValueError("validation must not auto-promote")
    if plan.get("decision_policy", {}).get("soft_validation_threshold") is not None:
        raise ValueError("do not invent a validation threshold")

    created = plan["created_from"]
    source = ROOT / created["strategy_path"]
    prereg = ROOT / created["preregistration"]
    if sha256_file(source) != created["strategy_sha256"]:
        raise ValueError("frozen strategy source drifted")
    if sha256_file(prereg) != created["preregistration_sha256"]:
        raise ValueError("preregistration drifted")

    spec = json.loads(prereg.read_text())
    candidate = plan["candidate"]
    if candidate["id"] != created["development_selected_id"]:
        raise ValueError("candidate differs from frozen development selection")
    if candidate["mode"] != "base" or candidate["family"] != "topology_migration":
        raise ValueError("unexpected validation candidate")
    if candidate["params"] != {"window": 84, "top_k": 5}:
        raise ValueError("validation parameters must remain frozen at w84/top_k5")
    if candidate["params"]["window"] not in spec["grid"]["window"]:
        raise ValueError("selected window absent from original preregistration")
    if created["strategy_path"] != spec["code_path"]:
        raise ValueError("strategy path differs from preregistration")

    fold = plan["validation_fold"]
    if fold != {
        "id": "validation",
        "start": "2023-01-01",
        "end": "2024-12-31",
        "use": "frozen chronological validation; never drives mutation",
    }:
        raise ValueError("validation fold changed")
    if plan.get("warmup_start") != "2022-01-01":
        raise ValueError("unexpected warmup start")
    if plan.get("costs") != [0.0, 0.04, 0.08, 0.12]:
        raise ValueError("cost ladder changed")
    if set(plan.get("context_controls", [])) != {"equal_liquid", "inverse_vol_trend", "persistent_low_vol"}:
        raise ValueError("context control set changed")
    return plan


def _metric_row(metrics: dict, fold_id: str = "validation") -> dict:
    return {cost: metrics[fold_id][cost] for cost in ("0.00", "0.04", "0.08", "0.12")}


def run(plan_path: Path, output: Path) -> Path:
    plan = load_plan(plan_path)
    output.mkdir(parents=True, exist_ok=True)
    access_mode = "unknown"
    try:
        ensure_local_data_access()
        access_mode = quantiacs_access_mode()
        import qnt.data as qndata
        import qnt.stats as qnstats

        fold = plan["validation_fold"]
        data = qndata.cryptodaily_load_data(min_date=plan["warmup_start"], max_date=fold["end"])
        data = data.sel(time=slice(plan["warmup_start"], fold["end"]))
        validate_panel(data, fold["start"], fold["end"])

        created = plan["created_from"]
        module = load_module(ROOT / created["strategy_path"])
        params = dict(plan["candidate"]["params"])
        fn = lambda panel: module.strategy(panel, params=params, mode="base")
        weights = fn(data)
        causality = check_causality(fn, data, full=weights)
        evaluator = QuantiacsEvaluator(data)
        metrics, _ = evaluator.evaluate(weights, [fold], plan["costs"])

        controls = {}
        for name in plan["context_controls"]:
            w = control_weights(data, name)
            cm, _ = evaluator.evaluate(w, [fold], plan["costs"])
            controls[name] = _metric_row(cm)

        packet = {
            "schema_version": 1,
            "status": "MEASURED_VALIDATION_REPORT_ONLY",
            "candidate": plan["candidate"],
            "validation_fold": fold,
            "metrics": _metric_row(metrics),
            "context_controls": controls,
            "causality": causality,
            "decision": {
                "automatic_promotion": False,
                "soft_validation_threshold": None,
                "note": "Report-only because the predeclared soft validation threshold is unset. Results must not drive strategy mutation.",
            },
            "provenance": {
                "plan_sha256": sha256_file(plan_path),
                "strategy_sha256": sha256_file(ROOT / created["strategy_path"]),
                "preregistration_sha256": sha256_file(ROOT / created["preregistration"]),
                "data_sha256": panel_hash(data),
                "toolbox_stats_sha256": sha256_file(qnstats.__file__),
                "quantiacs_access_mode": access_mode,
                "python": platform.python_version(),
                "numpy": np.__version__,
                "pandas": pd.__version__,
                "measured_utc": datetime.now(timezone.utc).isoformat(),
            },
        }
        run_dir = output / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        run_dir.mkdir()
        _write_json(run_dir / "validation.json", packet)
        lines = [
            "# Frozen topology-migration validation", "",
            "This packet evaluates the pre-selected `topology_migration_w84` implementation on the untouched 2023-2024 validation fold. It is report-only: no post-hoc validation threshold is invented.", "",
            "| Cost | Sharpe | Max DD | Avg turnover |", "|---:|---:|---:|---:|",
        ]
        for cost, row in packet["metrics"].items():
            lines.append(f"| {cost} | {row['sharpe_ratio'] if row['sharpe_ratio'] is not None else '—'} | {row['max_drawdown'] if row['max_drawdown'] is not None else '—'} | {row['avg_turnover'] if row['avg_turnover'] is not None else '—'} |")
        lines += ["", "Generic controls are context only; they are not a new selection set.", "", "No strategy mutation is permitted from this packet."]
        (run_dir / "report.md").write_text("\n".join(lines) + "\n")
        return run_dir
    except Exception as exc:
        run_dir = output / ("blocked_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
        run_dir.mkdir()
        _write_json(run_dir / "validation.json", {
            "status": "FAILED_SOFTWARE_OR_CAUSALITY",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "quantiacs_access_mode": access_mode,
        })
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--output", type=Path, default=ROOT / "results/topology_migration_validation")
    args = parser.parse_args()
    print(run(args.plan, args.output))


if __name__ == "__main__":
    main()
