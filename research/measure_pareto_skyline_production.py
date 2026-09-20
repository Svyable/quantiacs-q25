"""Production-mode validation for the frozen Pareto skyline submission."""
from __future__ import annotations

import json
import os
import time

import numpy as np

os.environ.setdefault("API_KEY", "default")

import qnt.backtester as qnbt
import qnt.data as qndata
import qnt.output as qnout
import qnt.stats as qnstats

from submissions import q25_pareto_skyline_multipass as s

START = "2016-01-01"
COSTS = (0.0, 0.04, 0.08, 0.12)
FIELDS = ("sharpe_ratio", "equity", "max_drawdown", "avg_turnover", "volatility")


def _clean(data, weights):
    return qnout.clean(weights, data, s.COMPETITION_TYPE).sel(time=slice(START, None))


def _ladder(data, weights):
    out = {}
    for cost in COSTS:
        stat = qnstats.calc_stat(
            data,
            weights,
            slippage_factor=cost,
            points_per_year=365,
        ).sel(time=slice(START, None))
        last = stat.isel(time=-1)
        out[f"{cost:.2f}"] = {
            key: float(last.sel(field=key).item())
            for key in FIELDS
            if key in last.field.values
        }
    return out


def main():
    started = time.perf_counter()
    result = qnbt.backtest(
        competition_type=s.COMPETITION_TYPE,
        load_data=s.load_data,
        lookback_period=s.LOOKBACK_DAYS,
        start_date=START,
        strategy=s.strategy,
        analyze=False,
        build_plots=False,
        check_correlation=False,
    )
    runtime = time.perf_counter() - started
    multi = result[0] if isinstance(result, tuple) else result

    data = qndata.cryptodaily_load_data(min_date="2015-01-01")
    single = s.calculate_weights(data, "pareto_le1")

    multi_clean = _clean(data, multi)
    single_clean = _clean(data, single)

    common_time = np.intersect1d(multi_clean.time.values, single_clean.time.values)
    common_asset = np.intersect1d(multi_clean.asset.values, single_clean.asset.values)
    m = multi_clean.sel(time=common_time, asset=common_asset)
    p = single_clean.sel(time=common_time, asset=common_asset)
    diff = np.abs(m.values - p.values)

    out = {
        "strategy_id": s.STRATEGY_ID,
        "submission_blob_expected": "04a3afd9b47525fd9a773455466a71494a393fc9",
        "evaluation": "full_history_production_multipass",
        "lookback_days": s.LOOKBACK_DAYS,
        "runtime_seconds": runtime,
        "parity": {
            "common_days": int(len(common_time)),
            "common_assets": int(len(common_asset)),
            "max_abs_weight_diff": float(np.nanmax(diff)) if diff.size else None,
            "mean_abs_weight_diff": float(np.nanmean(diff)) if diff.size else None,
            "nonzero_diff_count_gt_1e12": int(np.sum(diff > 1e-12)) if diff.size else None,
        },
        "multipass_cost_ladder": _ladder(data, multi_clean),
        "single_pass_cost_ladder": _ladder(data, single_clean),
    }
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
