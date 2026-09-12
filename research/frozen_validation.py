"""Frozen chronological validation for a pre-selected Q25 strategy.

The validation contract was frozen before opening 2023-2024, but that fold has now
been observed by the preregistered PR #22 workflow. The committed observation
sidecar is authoritative for evidence state. A normal invocation therefore refuses
to reopen the spent fold; ``--allow-replay`` exists only for exact reproducibility
and labels its output as a replay rather than fresh validation evidence.
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
DEFAULT_OBSERVED_STATUS = ROOT / "evidence/frontier_20260910b/forward_validation_2023_2024/observed_summary.json"


def _write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def load_plan(path: Path = DEFAULT_PLAN) -> dict:
    """Load the immutable contract that was frozen before a validation opening.

    The status string records the state at freeze time; current observation state is
    deliberately held in DEFAULT_OBSERVED_STATUS so the original contract need not
    be rewritten after returns are seen.
    """
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


def load_observed_status(path: Path = DEFAULT_OBSERVED_STATUS) -> dict | None:
    """Return durable observation state, or None only if the fold is truly unopened."""
    if not path.exists():
        return None
    observed = json.loads(path.read_text())
    if observed.get("evidence_stage") != "PREREGISTERED_FORWARD_OBSERVED":
        raise ValueError("unexpected validation evidence stage")
    if observed.get("fold_status") != "SPENT_DO_NOT_MUTATE":
        raise ValueError("unexpected validation fold status")
    if observed.get("validation_fold") != {"start": "2023-01-01", "end": "2024-12-31"}:
        raise ValueError("observed validation fold differs from frozen contract")
    if observed.get("mutation_policy", {}).get("retune_topology_migration_from_this_result") is not False:
        raise ValueError("observed status must forbid topology retuning")
    return observed


def validation_fold_is_spent(path: Path = DEFAULT_OBSERVED_STATUS) -> bool:
    return load_observed_status(path) is not None


def _metric_row(metrics: dict, fold_id: str = "validation") -> dict:
    return {cost: metrics[fold_id][cost] for cost in ("0.00", "0.04", "0.08", "0.12")}


def run(plan_path: Path, output: Path, *, allow_replay: bool = False) -> Path:
    plan = load_plan(plan_path)
    observed = load_observed_status()
    if observed is not None and not allow_replay:
        raise RuntimeError(
            "2023-2024 validation is already observed and permanently spent; "
            "use --allow-replay only to reproduce the frozen result"
        )

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
            "schema_version": 2,
            "status": "REPLAY_OF_SPENT_VALIDATION" if observed is not None else "MEASURED_VALIDATION_REPORT_ONLY",
            "fresh_evidence": observed is None,
            "candidate": plan["candidate"],
            "validation_fold": fold,
            "metrics": _metric_row(metrics),
            "context_controls": controls,
            "causality": causality,
            "decision": {
                "automatic_promotion": False,
                "soft_validation_threshold": None,
                "note": (
                    "Exact replay of an already-spent fold; cannot create new selection evidence."
                    if observed is not None
                    else "Report-only because the predeclared soft validation threshold is unset. Results must not drive strategy mutation."
                ),
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
                "prior_observation": str(DEFAULT_OBSERVED_STATUS.relative_to(ROOT)) if observed is not None else None,
            },
        }
        run_dir = output / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        run_dir.mkdir()
        _write_json(run_dir / "validation.json", packet)
        title = "# Frozen topology-migration validation replay" if observed is not None else "# Frozen topology-migration validation"
        boundary = (
            "This is an exact replay of the already-observed 2023-2024 fold. It is not a fresh validation look and cannot drive mutation or promotion."
            if observed is not None
            else "This packet evaluates the pre-selected `topology_migration_w84` implementation on the chronological 2023-2024 validation fold. It is report-only: no post-hoc validation threshold is invented."
        )
        lines = [title, "", boundary, "", "| Cost | Sharpe | Max DD | Avg turnover |", "|---:|---:|---:|---:|"]
        for cost, row in packet["metrics"].items():
            lines.append(f"| {cost} | {row['sharpe_ratio'] if row['sharpe_ratio'] is not None else '—'} | {row['max_drawdown'] if row['max_drawdown'] is not None else '—'} | {row['avg_turnover'] if row['avg_turnover'] is not None else '—'} |")
        lines += ["", "Generic controls are context only; they are not a new selection set.", "", "No strategy mutation is permitted from this packet."]
        (run_dir / "report.md").write_text("\n".join(lines) + "\n")
        return run_dir
    except Exception:
        # Refusal to reopen an already-spent fold occurs before this try block and
        # therefore does not masquerade as an infrastructure/software failure.
        run_dir = output / ("blocked_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
        run_dir.mkdir()
        _write_json(run_dir / "validation.json", {
            "status": "FAILED_SOFTWARE_OR_CAUSALITY",
            "quantiacs_access_mode": access_mode,
        })
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--output", type=Path, default=ROOT / "results/topology_migration_validation")
    parser.add_argument(
        "--allow-replay",
        action="store_true",
        help="explicitly replay the already-spent 2023-2024 fold for reproducibility; never fresh evidence",
    )
    args = parser.parse_args()
    print(run(args.plan, args.output, allow_replay=args.allow_replay))


if __name__ == "__main__":
    main()
