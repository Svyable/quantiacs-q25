"""Modern public-default recheck of frozen Q25 preparation candidates.

This is a contest-conversion harness, not a tuning loop. It evaluates only
already-frozen implementations/formulas and keeps selection evidence separate
from spent/diagnostic/full-pre-live submission screens.

Candidate provenance classes:
- C165 and V12: exact source mirrors already committed under strategies/champions.
- CoCrash126 and Trend_hit126: selector-only adapters of formulas embedded in
  the exact C165 preparation bundle. The adapter changes only the candidate
  selector/label; it is NOT claimed to be a byte-identical historical artifact.

No 2023+ result may mutate a formula, parameter, threshold, window, selector or
portfolio rule. Live data (2026-10-01 onward) is never evaluated here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import types
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

os.environ.setdefault("API_KEY", "default")

from research.benchmark import (  # noqa: E402
    FIELDS,
    QuantiacsEvaluator,
    check_platform_cleaned_weights,
    derived_return_metrics,
    load_module,
    panel_hash,
    selection_score,
    validate_panel,
)

ROOT = Path(__file__).resolve().parents[1]
C165_PATH = ROOT / "strategies" / "champions" / "03_c165_mobility_rotation.py"
V12_PATH = ROOT / "strategies" / "champions" / "04_v12_volume_diffusion.py"
FOLDS_PATH = ROOT / "configs" / "chronological_folds.yaml"
COSTS_PATH = ROOT / "configs" / "cost_ladder.yaml"
ROSTER_PATH = ROOT / "configs" / "historical_top10.yaml"
LIVE_START = pd.Timestamp("2026-10-01")
CONTEST_START = "2016-01-01"


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _selector_adapter_source(candidate_id: str) -> str:
    """Return C165 bundle source with exactly two selector tokens changed."""
    if candidate_id not in {"CoCrash126", "Trend_hit126"}:
        raise ValueError(candidate_id)
    text = C165_PATH.read_text()
    old_label = "CANDIDATE_ID = 'C165'"
    old_selector = "    CANDIDATE = 'C165'"
    if text.count(old_label) != 1 or text.count(old_selector) != 1:
        raise RuntimeError("C165 source no longer has the frozen selector shape")
    text = text.replace(old_label, f"CANDIDATE_ID = {candidate_id!r}", 1)
    text = text.replace(old_selector, f"    CANDIDATE = {candidate_id!r}", 1)
    return text


def load_candidate_module(candidate_id: str):
    if candidate_id == "C165":
        return load_module(C165_PATH), {
            "provenance_class": "EXACT_COMMITTED_MIRROR",
            "source_path": str(C165_PATH.relative_to(ROOT)),
            "source_sha256": sha256_path(C165_PATH),
            "selector_only_adapter": False,
        }
    if candidate_id == "V12":
        return load_module(V12_PATH), {
            "provenance_class": "EXACT_COMMITTED_MIRROR",
            "source_path": str(V12_PATH.relative_to(ROOT)),
            "source_sha256": sha256_path(V12_PATH),
            "selector_only_adapter": False,
        }
    if candidate_id in {"CoCrash126", "Trend_hit126"}:
        source = _selector_adapter_source(candidate_id)
        module = types.ModuleType(f"champion_{candidate_id.lower()}")
        module.__file__ = f"{C165_PATH}::{candidate_id}:selector-only"
        exec(compile(source, module.__file__, "exec"), module.__dict__)
        return module, {
            "provenance_class": "SELECTOR_ONLY_ADAPTER_FROM_C165_BUNDLE",
            "source_path": str(C165_PATH.relative_to(ROOT)),
            "source_sha256": sha256_path(C165_PATH),
            "selector_only_adapter": True,
            "adapter_change": "candidate label + embedded frozen-engine selector only",
            "formula_changed": False,
            "parameter_changed": False,
            "window_changed": False,
            "threshold_changed": False,
            "portfolio_rule_changed": False,
            "byte_identical_historical_artifact_claimed": False,
        }
    raise ValueError(candidate_id)


def _folds(pre_live_end: str) -> list[dict[str, Any]]:
    config = yaml.safe_load(FOLDS_PATH.read_text())
    by_id = {row["id"]: row for row in config["folds"]}
    rows = []
    for key in ("research", "dev", "validation"):
        row = dict(by_id[key])
        rows.append({"id": row["id"], "start": row["start"], "end": row["end"]})
    rows.append({"id": "diagnostic", "start": "2025-01-01", "end": pre_live_end})
    return rows


def _full_metrics(data, weights, end: str, costs: list[float]) -> dict[str, Any]:
    import qnt.output as qnout
    import qnt.stats as qnstats

    cleaned = qnout.clean(weights, data, "crypto_daily_long")
    cleaned = cleaned.sel(time=weights.time, asset=weights.asset).transpose("time", "asset")
    check_platform_cleaned_weights(cleaned, data)
    out: dict[str, Any] = {}
    for cost in costs:
        w = cleaned.sel(time=slice(CONTEST_START, end))
        d = data.sel(time=slice(None, end))
        stat = qnstats.calc_stat(d, w, slippage_factor=cost, points_per_year=365)
        row: dict[str, Any] = {}
        for field in FIELDS:
            number = float(stat.sel(field=field).isel(time=-1))
            row[field] = number if np.isfinite(number) else None
        rr = stat.sel(field="relative_return").to_pandas()
        extra = derived_return_metrics(rr)
        row.update(extra)
        dd = row["max_drawdown"]
        row["calmar_ratio"] = (
            extra["cagr"] / abs(dd)
            if extra["cagr"] is not None and dd is not None and dd < 0
            else None
        )
        out[f"{cost:.2f}"] = row
    return out


def _historical_reference() -> dict[str, Any]:
    roster = yaml.safe_load(ROSTER_PATH.read_text())
    wanted = {"C165", "V12", "CoCrash126", "Trend_hit126"}
    return {
        row["id"]: {
            "as_of": roster["as_of"],
            "metric_basis": roster["metric_basis"],
            "full_sharpe": row["full_sharpe"],
            "stress_sharpe": row["stress_sharpe"],
            "stress_atr_fraction": row["stress_atr_fraction"],
            "status": row["status"],
        }
        for row in roster["strategies"]
        if row["id"] in wanted
    }


def run(output: Path) -> dict[str, Any]:
    import qnt.data as qndata

    data = qndata.cryptodaily_load_data(min_date="2014-01-01")
    maximum = pd.Timestamp(data.time.values[-1])
    pre_live = min(maximum, LIVE_START - pd.Timedelta(days=1))
    if pre_live < pd.Timestamp("2025-01-01"):
        raise RuntimeError("public crypto history does not reach the diagnostic era")
    pre_live_end = pre_live.strftime("%Y-%m-%d")
    validate_panel(data.sel(time=slice(None, pre_live_end)), "2016-01-01", "2024-12-31")

    costs = [float(x) for x in yaml.safe_load(COSTS_PATH.read_text())["cost_ladder"]]
    folds = _folds(pre_live_end)
    evaluator = QuantiacsEvaluator(data.sel(time=slice(None, pre_live_end)))
    eval_data = evaluator.data

    packet: dict[str, Any] = {
        "schema_version": 1,
        "status": "LOCAL_PUBLIC_DEFAULT_FROZEN_RECHECK",
        "selection_policy": {
            "selection_folds": ["research", "dev"],
            "selection_score": "minimum Sharpe across research/dev and 4%,8%,12% cost rungs",
            "validation_2023_2024": "SPENT_DIAGNOSTIC_ONLY",
            "diagnostic_2025_plus": "CONTAMINATED_DIAGNOSTIC_ONLY",
            "full_pre_live": "SUBMISSION_GATE_SCREEN_ONLY_NOT_MODEL_SELECTION",
            "live_start": "2026-10-01",
            "mutation_after_observation": False,
        },
        "access_mode": "public_default",
        "data_end": pre_live_end,
        "data_sha256": panel_hash(eval_data),
        "cost_ladder": costs,
        "folds": folds,
        "historical_reference_separate_lane": _historical_reference(),
        "candidates": {},
    }

    for candidate_id in ("C165", "V12", "CoCrash126", "Trend_hit126"):
        print(f"\n=== {candidate_id} ===", flush=True)
        module, provenance = load_candidate_module(candidate_id)
        weights = module.calculate_weights(eval_data).transpose("time", "asset")
        measured, _returns = evaluator.evaluate(weights, folds, costs)
        robust = selection_score(measured)
        full = _full_metrics(eval_data, weights, pre_live_end, costs)
        full_04 = full.get("0.04", {}).get("sharpe_ratio")
        packet["candidates"][candidate_id] = {
            "provenance": provenance,
            "metrics": measured,
            "selection_robust_sharpe": robust,
            "selection_robust_floor_gt_1": bool(robust is not None and robust > 1.0),
            "full_pre_live_metrics": full,
            "local_full_is_sharpe_04": full_04,
            "local_submission_floor_gt_1": bool(full_04 is not None and full_04 > 1.0),
            "official_hosted_correlation_check": "PENDING",
            "submission": "PENDING",
        }
        print(
            json.dumps(
                {
                    "selection_robust_sharpe": robust,
                    "full_pre_live_sharpe_04": full_04,
                    "cleaner": measured.get("cleaner_impact", {}).get("status"),
                },
                indent=2,
            ),
            flush=True,
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(packet, indent=2, sort_keys=True, allow_nan=False))
    return packet


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/submission_sprint/champion_recheck.json")
    args = parser.parse_args()
    packet = run(Path(args.output))
    print("\n=== RECHECK SUMMARY ===")
    for candidate, row in packet["candidates"].items():
        print(
            f"{candidate:14s} robust={row['selection_robust_sharpe']!r} "
            f"full04={row['local_full_is_sharpe_04']!r} "
            f"floor={row['local_submission_floor_gt_1']}"
        )


if __name__ == "__main__":
    main()
