"""Development-only Q25 measurement for the frozen orthogonal alpha Pack2.

This evaluator intentionally stops at 2022-12-31. The repository's 2023-2024
validation fold is already spent, 2025+ is diagnostic-only, and the contest live
window remains untouched. No parameter search or post-observation mutation occurs
here.
"""
from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

import numpy as np
import xarray as xr

os.environ.setdefault("API_KEY", "default")

import qnt.data as qndata

from research.benchmark import (
    QuantiacsEvaluator,
    check_causality,
    check_weights,
    control_weights,
    panel_hash,
    policy,
    selection_score,
    validate_panel,
)
from research.preregister import sha256_file

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "experiments" / "orthogonal_alpha_pack_2_20260922" / "preregistration.json"
DATA_START = "2015-01-01"
SELECTION_START = "2016-01-01"
SELECTION_END = "2022-12-31"
SELECTION_FOLD = [{"id": "selection_2016_2022", "start": SELECTION_START, "end": SELECTION_END}]

CANDIDATES = {
    "q25_volatility_contraction_breakout_v1": "strategies.generated.q25_volatility_contraction_breakout",
    "q25_drawdown_recovery_v1": "strategies.generated.q25_drawdown_recovery",
    "q25_cross_sectional_dispersion_v1": "strategies.generated.q25_cross_sectional_dispersion",
    "q25_trend_consistency_v1": "strategies.generated.q25_trend_consistency",
}


def _strict_long_only(weights: xr.DataArray) -> None:
    minimum = float(weights.min().item())
    maximum = float(weights.max().item())
    gross = float(weights.sum("asset").max().item())
    if minimum < 0.0:
        raise AssertionError(f"negative raw weight: {minimum}")
    if maximum > 0.25 + 1e-12:
        raise AssertionError(f"name cap exceeded: {maximum}")
    if gross > 1.0 + 1e-12:
        raise AssertionError(f"gross cap exceeded: {gross}")


def _asset_order_invariance(fn, data: xr.DataArray, reference: xr.DataArray) -> dict:
    reversed_assets = data.asset.values[::-1]
    with xr.set_options(use_bottleneck=False):
        got = fn(data.sel(asset=reversed_assets)).sel(asset=data.asset.values)
    xr.testing.assert_allclose(reference, got, rtol=0.0, atol=1e-12)
    return {"status": "PASS", "atol": 1e-12}


def _determinism(fn, data: xr.DataArray, reference: xr.DataArray) -> dict:
    with xr.set_options(use_bottleneck=False):
        rerun = fn(data)
    xr.testing.assert_allclose(reference, rerun, rtol=0.0, atol=0.0)
    return {"status": "PASS", "atol": 0.0}


def _score_identity_permutation(weights: xr.DataArray, data: xr.DataArray) -> xr.DataArray:
    """Destroy score-to-asset identity while preserving the score distribution."""
    liquid = data.sel(field="is_liquid").transpose("time", "asset")
    liquid = xr.where(np.isfinite(liquid) & (liquid == 1), 1.0, 0.0)
    permuted = weights.roll(asset=1, roll_coords=False) * liquid
    return permuted.fillna(0.0).clip(min=0.0).transpose("time", "asset")


def _lookahead_detector(data: xr.DataArray) -> dict:
    """Verify the prefix checker rejects an intentionally future-looking signal."""

    def invalid_future_signal(d):
        close = d.sel(field="close").transpose("time", "asset").astype(float)
        liquid0 = d.sel(field="is_liquid").transpose("time", "asset")
        liquid = xr.where((liquid0 == 1) & np.isfinite(close) & (close > 0), 1.0, 0.0)
        future_return = close.shift(time=-1) / close - 1.0
        raw = xr.where(future_return > 0.0, 1.0, 0.0) * liquid
        gross = raw.sum("asset")
        return xr.where(gross > 0.0, raw / gross, 0.0).clip(min=0.0).transpose("time", "asset")

    try:
        check_causality(invalid_future_signal, data, checkpoints=9)
    except ValueError:
        return {"status": "PASS", "meaning": "intentional +1-day lookahead was rejected"}
    raise AssertionError("causality checker failed to reject intentional +1-day lookahead")


def _selection(metrics: dict) -> dict:
    return metrics["selection_2016_2022"]


def _sharpe(metrics: dict, cost: str) -> float | None:
    return _selection(metrics)[cost]["sharpe_ratio"]


def main() -> None:
    folds, costs = policy()
    if folds[-1]["end"] != SELECTION_END:
        raise AssertionError("development policy changed; refusing to widen the data window")

    data = qndata.cryptodaily_load_data(min_date=DATA_START, max_date=SELECTION_END)
    data = data.sel(time=slice(DATA_START, SELECTION_END))
    validate_panel(data, SELECTION_START, SELECTION_END)
    if str(data.time.values[-1])[:10] > SELECTION_END:
        raise AssertionError("holdout data entered development measurement")

    evaluator = QuantiacsEvaluator(data)
    prereg = json.loads(PREREG.read_text())
    declared = {c["id"] for c in prereg["candidates"]}
    if declared != set(CANDIDATES):
        raise AssertionError("candidate roster differs from frozen preregistration")

    baseline_weights = control_weights(data, "equal_liquid")
    baseline_dev, _ = evaluator.evaluate(baseline_weights, folds, costs)
    baseline_selection, _ = evaluator.evaluate(baseline_weights, SELECTION_FOLD, costs)

    report = {
        "schema_version": 1,
        "experiment_id": prereg["experiment_id"],
        "evidence_stage": "DEVELOPMENT_ONLY_2016_2022",
        "quantiacs_access_mode": "public_default",
        "data": {
            "min_date": str(data.time.values[0])[:10],
            "max_date": str(data.time.values[-1])[:10],
            "sha256": panel_hash(data),
            "holdout_2023_plus_loaded": False,
        },
        "preregistration_sha256": sha256_file(PREREG),
        "cost_ladder": costs,
        "baseline_equal_liquid": {
            "research_dev": baseline_dev,
            "selection_2016_2022": _selection(baseline_selection),
        },
        "lookahead_destructive_control": _lookahead_detector(data),
        "candidates": {},
    }

    for candidate_id, module_name in CANDIDATES.items():
        module = importlib.import_module(module_name)
        fn = module.calculate_weights

        with xr.set_options(use_bottleneck=False):
            weights = fn(data)
        check_weights(weights, data)
        _strict_long_only(weights)

        mechanics = {
            "strict_long_only_liquid_caps": "PASS",
            "prefix_and_bounded_replay": check_causality(fn, data, full=weights, checkpoints=9),
            "asset_order_invariance": _asset_order_invariance(fn, data, weights),
            "determinism": _determinism(fn, data, weights),
        }

        research_dev, _ = evaluator.evaluate(weights, folds, costs)
        selection, _ = evaluator.evaluate(weights, SELECTION_FOLD, costs)

        permuted_weights = _score_identity_permutation(weights, data)
        check_weights(permuted_weights, data)
        _strict_long_only(permuted_weights)
        permuted_selection, _ = evaluator.evaluate(permuted_weights, SELECTION_FOLD, costs)

        selection_metrics = _selection(selection)
        permuted_metrics = _selection(permuted_selection)
        base_4 = selection_metrics["0.04"]["sharpe_ratio"]
        perm_4 = permuted_metrics["0.04"]["sharpe_ratio"]
        dev_4 = research_dev["dev"]["0.04"]["sharpe_ratio"]
        mechanics_pass = all(
            item == "PASS" or (isinstance(item, dict) and item.get("status") == "PASS")
            for item in mechanics.values()
        )
        gates = {
            "selection_2016_2022_sharpe_0p04_gt_1": bool(base_4 is not None and base_4 > 1.0),
            "development_2021_2022_sharpe_0p04_gt_0": bool(dev_4 is not None and dev_4 > 0.0),
            "all_mechanics_checks_pass": mechanics_pass,
            "score_identity_permutation_weaker_at_0p04": bool(
                base_4 is not None and perm_4 is not None and base_4 > perm_4
            ),
            "no_holdout_retuning": True,
        }

        if not mechanics_pass:
            decision = "INVALID_MECHANICS"
        elif not gates["selection_2016_2022_sharpe_0p04_gt_1"] or not gates["development_2021_2022_sharpe_0p04_gt_0"]:
            decision = "FREEZE_WEAK_DEVELOPMENT"
        elif not gates["score_identity_permutation_weaker_at_0p04"]:
            decision = "FALSIFIED_BY_IDENTITY_PERMUTATION"
        else:
            decision = "ADVANCE_TO_HARDENING_NO_RETUNE"

        source_path = ROOT / module.__file__
        report["candidates"][candidate_id] = {
            "module": module_name,
            "source_sha256": sha256_file(source_path),
            "mechanics": mechanics,
            "research_dev": research_dev,
            "selection_score_min_research_dev_costs_0p04_0p08_0p12": selection_score(research_dev),
            "selection_2016_2022": selection_metrics,
            "score_identity_permutation_selection_2016_2022": permuted_metrics,
            "gates": gates,
            "decision": decision,
        }

    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
