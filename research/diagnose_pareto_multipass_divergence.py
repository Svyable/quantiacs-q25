"""Diagnose sparse Pareto skyline single-vs-multipass divergences.

Diagnostic only. This script must not change or select strategy parameters.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np

os.environ.setdefault("API_KEY", "default")

import qnt.backtester as qnbt
import qnt.data as qndata
import qnt.output as qnout

from submissions import q25_pareto_skyline_multipass as s

START = "2016-01-01"
TOL = 1e-12


def _clean(data, weights):
    return qnout.clean(weights, data, s.COMPETITION_TYPE).sel(time=slice(START, None))


def _iso(v):
    return np.datetime_as_string(np.datetime64(v), unit="D")


def _last_features(data):
    _, liq, s7, vol, trend, mom, dd = s._features(data)
    return {
        "liquid": liq.isel(time=-1),
        "s7": s7.isel(time=-1),
        "vol14": vol.isel(time=-1),
        "trend": trend.isel(time=-1),
        "mom14": mom.isel(time=-1),
        "dd30": dd.isel(time=-1),
    }


def _safe_float(v):
    x = float(v)
    return x if np.isfinite(x) else None


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

    mc = _clean(data, multi)
    sc = _clean(data, single)
    common_time = np.intersect1d(mc.time.values, sc.time.values)
    common_asset = np.intersect1d(mc.asset.values, sc.asset.values)
    m = mc.sel(time=common_time, asset=common_asset)
    p = sc.sel(time=common_time, asset=common_asset)
    diff = np.abs(m.values - p.values)

    idx = np.argwhere(diff > TOL)
    rows = []
    for ti, ai in idx:
        rows.append({
            "time": _iso(common_time[ti]),
            "asset": str(common_asset[ai]),
            "abs_diff": float(diff[ti, ai]),
            "multipass_clean": float(m.values[ti, ai]),
            "single_clean": float(p.values[ti, ai]),
        })
    rows.sort(key=lambda r: r["abs_diff"], reverse=True)

    date_diagnostics = {}
    for date in sorted({r["time"] for r in rows}):
        dt = np.datetime64(date)
        prefix = data.sel(time=slice(None, date))
        # Match qnt.backtester.standard_window exactly: calendar-day lookback,
        # inclusive at both ends. Do not approximate it as the last N rows.
        tail = qnbt.standard_window(prefix, dt, s.LOOKBACK_DAYS)

        w_full_all = s.strategy(prefix).sel(asset=common_asset)
        w_tail_all = s.strategy(tail).sel(asset=common_asset)
        w_full = w_full_all.sel(time=dt)
        w_tail = w_tail_all.sel(time=dt)
        wd = np.abs(w_full.values - w_tail.values)

        ff = _last_features(prefix)
        tf = _last_features(tail)
        assets_here = sorted({r["asset"] for r in rows if r["time"] == date})
        feature_rows = {}
        for asset in assets_here:
            feature_rows[asset] = {}
            for key in ff:
                a = ff[key].sel(asset=asset).item()
                b = tf[key].sel(asset=asset).item()
                af = _safe_float(a)
                bf = _safe_float(b)
                feature_rows[asset][key] = {
                    "full": af,
                    "tail": bf,
                    "abs_diff": (
                        abs(af - bf)
                        if af is not None and bf is not None
                        else None
                    ),
                }

        path_start = dt - np.timedelta64(2, "D")
        path_times = np.intersect1d(
            w_full_all.sel(time=slice(path_start, dt)).time.values,
            w_tail_all.sel(time=slice(path_start, dt)).time.values,
        )
        smoothing_path = []
        for path_dt in path_times:
            wf = w_full_all.sel(time=path_dt)
            wt = w_tail_all.sel(time=path_dt)
            pdiff = np.abs(wf.values - wt.values)
            smoothing_path.append({
                "time": _iso(path_dt),
                "max_abs_diff": float(np.nanmax(pdiff)),
                "nonzero_count_gt_1e12": int(np.sum(pdiff > TOL)),
            })

        date_diagnostics[date] = {
            "tail_start": _iso(tail.time.values[0]),
            "tail_observations": int(tail.sizes["time"]),
            "raw_weight_max_abs_diff_full_vs_tail": float(np.nanmax(wd)),
            "raw_weight_nonzero_count_gt_1e12": int(np.sum(wd > TOL)),
            "raw_differences": [
                {
                    "asset": str(common_asset[i]),
                    "full": float(w_full.values[i]),
                    "tail": float(w_tail.values[i]),
                    "abs_diff": float(wd[i]),
                }
                for i in np.where(wd > TOL)[0]
            ],
            "features_on_clean_diff_assets": feature_rows,
            "three_day_smoothed_weight_path": smoothing_path,
        }

    out = {
        "strategy_id": s.STRATEGY_ID,
        "submission_blob": "d829f1c78ec8b27a30eccbb8cee231d6d02e63fd",
        "diagnostic_only": True,
        "runtime_seconds": runtime,
        "backtester_window_semantics": "calendar_days_inclusive",
        "common_days": int(len(common_time)),
        "common_assets": int(len(common_asset)),
        "clean_diff_count_gt_1e12": int(len(rows)),
        "clean_max_abs_diff": float(np.nanmax(diff)) if diff.size else None,
        "clean_differences": rows,
        "date_diagnostics": date_diagnostics,
    }
    path = Path("results/pareto_skyline_20260919/parity_diagnostic.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
