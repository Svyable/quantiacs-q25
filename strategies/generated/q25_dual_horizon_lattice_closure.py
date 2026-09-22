"""Q25 dual-horizon lattice-closure research strategy.

Experiment: lattice_closure_20260921

This candidate is a geometry refinement of the frozen Pareto-skyline family.
It keeps the incumbent fast Pareto score and broad positive-state gate, then
constructs two causal skyline states over the same five economic dimensions at
fast and exactly doubled horizons. The states are combined in the subset
lattice:

    root  = broad positive-state candidates
    fast  = root ∩ fast Pareto <= 1-dominator skyline
    slow  = root ∩ slow Pareto <= 1-dominator skyline
    meet  = fast ∩ slow
    join  = fast ∪ slow

The terminal state is the deepest state that does not destroy cap-filling
capacity: use meet when it retains enough candidates, otherwise join, otherwise
root. "Enough" is derived from the 25% name cap: four names can fill gross 1.0;
when root itself has fewer than four names, the resolver merely requires that a
refinement preserve all root candidates. No return-driven parameter search is
embedded in the strategy.

The structural inspiration is abstract interpretation / lattice deduction:
refine toward more informative states, detect a conflict when refinement
eliminates too much admissible capacity, and ascend to a sounder approximation.
This is not a learned LDT and inherits no formal soundness guarantee.

Only Quantiacs cryptodaily OHLCV + historical is_liquid are used. The strategy
is automatic, long-only, liquid-only, deterministic, symbol-agnostic, capped at
25% per asset, and allows cash.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
STRATEGY_ID = "q25_dual_horizon_lattice_closure_v1"
EXPERIMENT_ID = "lattice_closure_20260921"
RESEARCH_START = "2016-01-01"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
CAPACITY_NAMES = int(round(1.0 / NAME_CAP))
EPS = 1e-12


def _close_liquid(data):
    close = data.sel(field="close").transpose("time", "asset").astype(float)
    z = data.sel(field="is_liquid").transpose("time", "asset")
    liquid = xr.where((z == 1) & np.isfinite(close) & (close > 0), 1.0, 0.0)
    return close, liquid


def _returns(close):
    r = close / close.shift(time=1) - 1.0
    return xr.where(np.isfinite(r), r, 0.0)


def _rolling_values(x, n, m):
    """Explicit trailing windows make arithmetic invariant to supplied prefix length."""
    if x.sizes["time"] < m:
        return None, None
    width = min(n, x.sizes["time"])
    values = x.rolling(time=width).construct("_window")
    enough = values.count("_window") >= m
    return values, enough


def _sma(x, n, m):
    values, enough = _rolling_values(x, n, m)
    if values is None:
        return xr.full_like(x, np.nan, dtype=float)
    return values.mean("_window", skipna=True).where(enough)


def _std(x, n, m):
    values, enough = _rolling_values(x, n, m)
    if values is None:
        return xr.full_like(x, np.nan, dtype=float)
    return values.std("_window", skipna=True, ddof=0).where(enough)


def _max(x, n, m):
    if x.sizes["time"] < m:
        return xr.full_like(x, np.nan, dtype=float)
    return x.rolling(time=min(n, x.sizes["time"]), min_periods=m).max()


def _canonical_assets(x):
    return np.sort(np.asarray(x.asset.values).astype(str))


def _mean(x, liquid):
    assets = _canonical_assets(x)
    xo = x.sel(asset=assets)
    lo = liquid.sel(asset=assets)
    safe = xr.where(np.isfinite(xo), xo, 0.0)
    n = lo.sum("asset")
    return xr.where(n > 0, (safe * lo).sum("asset") / n, 0.0)


def _std_cs(x, liquid):
    assets = _canonical_assets(x)
    xo = x.sel(asset=assets)
    lo = liquid.sel(asset=assets)
    mean = _mean(xo, lo)
    safe = xr.where(np.isfinite(xo), xo, 0.0)
    n = lo.sum("asset")
    var = xr.where(n > 0, (((safe - mean) ** 2) * lo).sum("asset") / n, 0.0)
    return np.sqrt(xr.where(var > 0, var, 0.0))


def _allocate(raw, liquid):
    original_assets = raw.asset.values
    assets = _canonical_assets(raw)
    ro = raw.sel(asset=assets)
    lo = liquid.sel(asset=assets)
    ro = xr.where(np.isfinite(ro) & (ro > 0), ro, 0.0) * lo
    gross = ro.sum("asset")
    w = xr.where(gross > EPS, ro / gross, 0.0)
    w = xr.where(w > NAME_CAP, NAME_CAP, w) * lo
    return (
        w.sel(asset=original_assets)
        .transpose("time", "asset")
        .fillna(0.0)
        .reset_coords("field", drop=True)
    )


def _feature_panel(close, liquid, *, scale: int):
    """Five-dimensional Pareto panel; scale=1 is the incumbent geometry, scale=2 doubles horizons."""
    if scale not in (1, 2):
        raise ValueError("scale must be 1 or 2")
    r = _returns(close)
    mu = _sma(r, 7 * scale, 5 * scale)
    vol = _std(r, 14 * scale, 7 * scale)
    sharpe = np.sqrt(365.0) * mu / (vol + EPS)
    sma_fast = _sma(close, 12 * scale, 8 * scale)
    sma_slow = _sma(close, 48 * scale, 24 * scale)
    trend = sma_fast / (sma_slow + EPS) - 1.0
    momentum = close / close.shift(time=14 * scale) - 1.0
    peak = _max(close, 30 * scale, 15 * scale)
    drawdown = close / (peak + EPS) - 1.0
    valid = liquid * xr.where(
        np.isfinite(sharpe)
        & np.isfinite(vol)
        & np.isfinite(trend)
        & np.isfinite(momentum)
        & np.isfinite(drawdown),
        1.0,
        0.0,
    )
    return {
        "sharpe": sharpe,
        "vol": vol,
        "trend": trend,
        "momentum": momentum,
        "drawdown": drawdown,
        "valid": valid,
    }


def _dominance_count(liquid, panel):
    original_assets = liquid.asset.values
    assets = _canonical_assets(liquid)
    lo = liquid.sel(asset=assets)
    aligned = xr.concat(
        [
            panel["sharpe"].sel(asset=assets),
            panel["trend"].sel(asset=assets),
            panel["momentum"].sel(asset=assets),
            panel["drawdown"].sel(asset=assets),
            -panel["vol"].sel(asset=assets),
        ],
        dim="feature",
    ).transpose("time", "asset", "feature")
    vals = aligned.values.astype(float)
    valid = (lo.values > 0) & np.isfinite(vals).all(axis=2)
    left = vals[:, :, None, :]
    right = vals[:, None, :, :]
    dominates = (left >= right).all(axis=3) & (left > right).any(axis=3)
    dominates &= valid[:, :, None] & valid[:, None, :]
    # counts[t, j] = number of liquid peers i that dominate asset j.
    counts = dominates.sum(axis=1).astype(float)
    return xr.DataArray(
        counts,
        dims=("time", "asset"),
        coords={"time": lo.time.values, "asset": assets},
        name="dominance_count",
    ).sel(asset=original_assets)


def _states(data):
    close, liquid = _close_liquid(data)
    fast = _feature_panel(close, liquid, scale=1)
    slow = _feature_panel(close, liquid, scale=2)
    fast_counts = _dominance_count(liquid, fast)
    slow_counts = _dominance_count(liquid, slow)

    mean_s = _mean(fast["sharpe"], liquid)
    sd_s = _std_cs(fast["sharpe"], liquid)
    base_root = (
        (fast["trend"] > 0.0)
        & (fast["momentum"] > 0.0)
        & (fast["drawdown"] > -0.22)
        & (fast["vol"] > 0.0)
        & (fast["sharpe"] > mean_s)
        & (fast["valid"] > 0)
    )
    base_fast_state = base_root & (fast_counts <= 1.0)
    # The new dual-horizon mechanism only starts once the slow panel is valid.
    # The frozen fast-only control remains byte-for-formula equivalent to the
    # incumbent and therefore does not inherit this extra warmup requirement.
    root = base_root & (slow["valid"] > 0)
    fast_state = root & (fast_counts <= 1.0)
    slow_state = root & (slow_counts <= 1.0)
    meet = fast_state & slow_state
    join = fast_state | slow_state

    quality = xr.where(
        fast["sharpe"] > mean_s,
        (fast["sharpe"] - mean_s + 0.10 * sd_s).clip(min=0.0),
        0.0,
    )
    score = (quality ** 1.20) / (fast["vol"] + 0.015)
    score = xr.where(np.isfinite(score), score, 0.0) * liquid
    return liquid, score, root, base_fast_state, fast_state, slow_state, meet, join, slow_counts


def _resolve(root, meet, join):
    """Choose the most precise state that preserves cap-filling capacity."""
    root_n = root.astype(float).sum("asset")
    required = xr.where(root_n >= CAPACITY_NAMES, float(CAPACITY_NAMES), root_n)
    meet_n = meet.astype(float).sum("asset")
    join_n = join.astype(float).sum("asset")
    chosen = xr.where(meet_n >= required, meet, xr.where(join_n >= required, join, root))
    return chosen.astype(float)


def calculate_weights(data, mode="closure"):
    (
        liquid,
        score,
        root,
        base_fast_state,
        fast_state,
        slow_state,
        meet,
        join,
        slow_counts,
    ) = _states(data)

    if mode == "closure":
        mask = _resolve(root, meet, join)
    elif mode == "base_pareto":
        mask = base_fast_state.astype(float)
    elif mode == "root_only":
        mask = root.astype(float)
    elif mode == "meet_only":
        mask = meet.astype(float)
    elif mode == "join_only":
        mask = join.astype(float)
    elif mode == "slow_only":
        mask = slow_state.astype(float)
    elif mode == "anti_slow":
        # Destructive direction control: keep fast-skyline names that the slow
        # geometry explicitly classifies as dominated by at least two peers.
        mask = (fast_state & (slow_counts >= 2.0)).astype(float)
    else:
        raise ValueError(f"unknown mode: {mode}")

    raw = _sma(score * mask, 3, 1) * mask * liquid
    return _allocate(raw, liquid)


def strategy(data):
    return calculate_weights(data, "closure")


def load_data(period):
    os.environ.setdefault("API_KEY", "default")
    import qnt.data as qndata
    return qndata.cryptodaily_load_data(tail=max(int(period), LOOKBACK_DAYS))


def _snapshot(stat):
    if stat.sizes.get("time", 0) == 0:
        return {}
    row = stat.isel(time=-1).to_pandas()
    out = {}
    for field in (
        "sharpe_ratio",
        "mean_return",
        "volatility",
        "max_drawdown",
        "equity",
        "avg_turnover",
    ):
        if field in row.index:
            value = float(row[field])
            out[field] = value if np.isfinite(value) else None
    return out


def run_research(output=None):
    os.environ.setdefault("API_KEY", "default")
    import qnt.data as qndata
    import qnt.output as qnout
    import qnt.stats as qnstats

    data = qndata.cryptodaily_load_data(min_date="2015-01-01")
    modes = (
        "base_pareto",
        "root_only",
        "meet_only",
        "join_only",
        "slow_only",
        "anti_slow",
        "closure",
    )
    folds = {
        "research_2016_2020": ("2016-01-01", "2020-12-31"),
        "dev_2021_2022": ("2021-01-01", "2022-12-31"),
        "selection_2016_2022": ("2016-01-01", "2022-12-31"),
        "spent_validation_2023_2024": ("2023-01-01", "2024-12-31"),
        "diagnostic_2025_plus": ("2025-01-01", None),
        "full_2016_plus": ("2016-01-01", None),
    }
    payload = {
        "experiment_id": EXPERIMENT_ID,
        "strategy_id": STRATEGY_ID,
        "evidence_class": "PREREGISTERED_PARETO_GEOMETRY_REFINEMENT",
        "selection_cutoff": "2022-12-31",
        "post_2022_may_not_drive_parameter_tuning": True,
        "modes": {},
    }
    for mode in modes:
        print(f"calculating {mode}", flush=True)
        raw = calculate_weights(data, mode).sel(time=slice(RESEARCH_START, None))
        clean = qnout.clean(raw, data, COMPETITION_TYPE, debug=False)
        clean = clean.sel(time=raw.time, asset=raw.asset)
        result = {}
        for fold_name, (start, end) in folds.items():
            result[fold_name] = {}
            for cost in (0.04, 0.08, 0.12):
                weights = clean.sel(time=slice(start, end))
                stat_data = data.sel(time=slice(None, end))
                stat = qnstats.calc_stat(
                    stat_data,
                    weights,
                    slippage_factor=cost,
                    points_per_year=365,
                ).sel(time=slice(start, end))
                result[fold_name][f"{cost:.2f}"] = _snapshot(stat)
        payload["modes"][mode] = result
        print(json.dumps({mode: result}, indent=2, sort_keys=True), flush=True)

    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return payload


def run_multipass(check_correlation=False):
    os.environ.setdefault("API_KEY", "default")
    import qnt.backtester as qnbt
    return qnbt.backtest(
        competition_type=COMPETITION_TYPE,
        load_data=load_data,
        lookback_period=LOOKBACK_DAYS,
        start_date=RESEARCH_START,
        strategy=strategy,
        analyze=True,
        build_plots=False,
        check_correlation=check_correlation,
    )


def _main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research", action="store_true")
    parser.add_argument("--multipass", action="store_true")
    parser.add_argument("--check-correlation", action="store_true")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    if args.research:
        run_research(args.output)
    elif args.multipass:
        run_multipass(args.check_correlation)
    else:
        parser.print_help()


if __name__ == "__main__":
    _main()
