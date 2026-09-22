"""Q25 Pareto-skyline research strategy.

Pure-crypto long-only candidate. Each liquid asset is represented by five causal
state dimensions: short-horizon risk-adjusted return, medium trend, momentum,
drawdown resilience, and inverse volatility. The candidate uses a partial order:
asset A dominates B when A is at least as good on every dimension and strictly
better on at least one. The central book keeps the first two skyline layers
(dominated by at most one peer), then applies broad positive-state gates.

This is a deterministic cross-sectional geometry, not a learned model.
Only Quantiacs crypto daily OHLCV + historical is_liquid are used.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
STRATEGY_ID = "q25_pareto_skyline_v1"
EXPERIMENT_ID = "pareto_skyline_20260919"
RESEARCH_START = "2016-01-01"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
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
    """Construct explicit trailing windows for prefix-length-invariant arithmetic."""
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


def _sma_frozen(x, n, m):
    if x.sizes["time"] < m:
        return xr.full_like(x, np.nan, dtype=float)
    return x.rolling(time=min(n, x.sizes["time"]), min_periods=m).mean()


def _std_frozen(x, n, m):
    if x.sizes["time"] < m:
        return xr.full_like(x, np.nan, dtype=float)
    return x.rolling(time=min(n, x.sizes["time"]), min_periods=m).std()


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
    n = lo.sum("asset")
    safe = xr.where(np.isfinite(xo), xo, 0.0)
    var = xr.where(
        n > 0,
        (((safe - mean) ** 2) * lo).sum("asset") / n,
        0.0,
    )
    return np.sqrt(xr.where(var > 0, var, 0.0))


def _allocate(raw, liquid):
    original_assets = raw.asset.values
    assets = _canonical_assets(raw)
    ro = xr.where(
        np.isfinite(raw.sel(asset=assets)) & (raw.sel(asset=assets) > 0),
        raw.sel(asset=assets),
        0.0,
    )
    lo = liquid.sel(asset=assets)
    ro = ro * lo
    gross = ro.sum("asset")
    w = xr.where(gross > EPS, ro / gross, 0.0)
    w = xr.where(w > NAME_CAP, NAME_CAP, w) * lo
    w = w.sel(asset=original_assets)
    return w.transpose("time", "asset").fillna(0.0).reset_coords("field", drop=True)


# Exact legacy reduction/allocation path used only by the frozen Sharpe7 control.
# Keeping these separate preserves byte-for-formula numerical parity with the
# promoted submission while the new Pareto family uses canonical reductions.
def _mean_frozen(x, liquid):
    safe = xr.where(np.isfinite(x), x, 0.0)
    n = liquid.sum("asset")
    return xr.where(n > 0, (safe * liquid).sum("asset") / n, 0.0)


def _std_cs_frozen(x, liquid):
    mean = _mean_frozen(x, liquid)
    n = liquid.sum("asset")
    var = xr.where(
        n > 0,
        (((xr.where(np.isfinite(x), x, 0.0) - mean) ** 2) * liquid).sum("asset") / n,
        0.0,
    )
    return np.sqrt(xr.where(var > 0, var, 0.0))


def _allocate_frozen(raw, liquid):
    raw = xr.where(np.isfinite(raw) & (raw > 0), raw, 0.0) * liquid
    gross = raw.sum("asset")
    w = xr.where(gross > EPS, raw / gross, 0.0)
    w = xr.where(w > NAME_CAP, NAME_CAP, w) * liquid
    return w.transpose("time", "asset").fillna(0.0).reset_coords("field", drop=True)


def _features(data):
    close, liquid = _close_liquid(data)
    r = _returns(close)
    mu7 = _sma(r, 7, 5)
    vol14 = _std(r, 14, 7)
    s7 = np.sqrt(365.0) * mu7 / (vol14 + EPS)
    sma12 = _sma(close, 12, 8)
    sma48 = _sma(close, 48, 24)
    trend = sma12 / (sma48 + EPS) - 1.0
    mom14 = close / close.shift(time=14) - 1.0
    peak30 = _max(close, 30, 15)
    dd30 = close / (peak30 + EPS) - 1.0
    return close, liquid, s7, vol14, trend, mom14, dd30


def _dominance_count(liquid, s7, vol14, trend, mom14, dd30):
    original_assets = liquid.asset.values
    assets = _canonical_assets(liquid)
    lo = liquid.sel(asset=assets)
    aligned = xr.concat(
        [
            s7.sel(asset=assets),
            trend.sel(asset=assets),
            mom14.sel(asset=assets),
            dd30.sel(asset=assets),
            -vol14.sel(asset=assets),
        ],
        dim="feature",
    ).transpose("time", "asset", "feature")
    vals = aligned.values.astype(float)
    valid = ((lo.values > 0) & np.isfinite(vals).all(axis=2))
    left = vals[:, :, None, :]
    right = vals[:, None, :, :]
    dom = (left >= right).all(axis=3) & (left > right).any(axis=3)
    dom &= valid[:, :, None] & valid[:, None, :]
    counts = dom.sum(axis=1).astype(float)
    counts_da = xr.DataArray(
        counts,
        dims=("time", "asset"),
        coords={"time": lo.time.values, "asset": assets},
        name="dominance_count",
    ).sel(asset=original_assets)
    valid_da = xr.DataArray(
        valid.astype(float),
        dims=("time", "asset"),
        coords={"time": lo.time.values, "asset": assets},
        name="valid_features",
    ).sel(asset=original_assets)
    return counts_da, valid_da


def _base_sharpe7(data):
    close, liquid = _close_liquid(data)
    r = _returns(close)
    mu7 = _sma_frozen(r, 7, 5)
    vol14 = _std_frozen(r, 14, 7)
    s7 = np.sqrt(365.0) * mu7 / (vol14 + EPS)
    sma12 = _sma_frozen(close, 12, 8)
    sma48 = _sma_frozen(close, 48, 24)
    mom14 = close / close.shift(time=14) - 1.0
    peak30 = _max(close, 30, 15)
    dd30 = close / (peak30 + EPS) - 1.0
    mean = _mean_frozen(s7, liquid)
    sd = _std_cs_frozen(s7, liquid)
    hurdle = mean + 0.20 * sd
    quality = xr.where(s7 > hurdle, s7 - hurdle, 0.0)
    gate = (sma12 > sma48) & (mom14 > 0.0) & (dd30 > -0.22) & (vol14 > 0.0)
    raw = xr.where(gate, (quality.clip(min=0.0) ** 1.25) / (vol14 + 0.015), 0.0) * liquid
    raw = _sma_frozen(raw, 3, 1) * liquid
    return _allocate_frozen(raw, liquid)


def calculate_weights(data, mode="pareto_le1"):
    close, liquid, s7, vol14, trend, mom14, dd30 = _features(data)

    if mode == "base_sharpe7":
        return _base_sharpe7(data)

    counts, valid = _dominance_count(liquid, s7, vol14, trend, mom14, dd30)
    mean_s = _mean(s7, liquid)
    sd_s = _std_cs(s7, liquid)
    broad_gate = (
        (trend > 0.0)
        & (mom14 > 0.0)
        & (dd30 > -0.22)
        & (vol14 > 0.0)
        & (s7 > mean_s)
    )
    quality = xr.where(s7 > mean_s, (s7 - mean_s + 0.10 * sd_s).clip(min=0.0), 0.0)
    score = (quality ** 1.20) / (vol14 + 0.015)

    if mode == "pareto_le1":
        skyline = counts <= 1.0
    elif mode == "frontier_only":
        skyline = counts <= 0.0
    elif mode == "no_pareto":
        skyline = xr.ones_like(counts, dtype=bool)
    elif mode == "dominated_tail":
        skyline = counts >= 2.0
    elif mode == "pareto_le2":
        skyline = counts <= 2.0
    else:
        raise ValueError(mode)

    raw = xr.where(broad_gate & skyline & (valid > 0), score, 0.0) * liquid
    raw = _sma(raw, 3, 1) * liquid
    return _allocate(raw, liquid)


def strategy(data):
    return calculate_weights(data, "pareto_le1")


def load_data(period):
    os.environ.setdefault("API_KEY", "default")
    import qnt.data as qndata
    return qndata.cryptodaily_load_data(tail=max(int(period), LOOKBACK_DAYS))


def _snapshot(stat):
    if stat.sizes.get("time", 0) == 0:
        return {}
    row = stat.isel(time=-1).to_pandas()
    out = {}
    for field in ("sharpe_ratio", "mean_return", "volatility", "max_drawdown", "equity", "avg_turnover"):
        if field in row.index:
            v = float(row[field])
            out[field] = v if np.isfinite(v) else None
    return out


def run_research(output=None):
    os.environ.setdefault("API_KEY", "default")
    import qnt.data as qndata
    import qnt.output as qnout
    import qnt.stats as qnstats

    data = qndata.cryptodaily_load_data(min_date="2015-01-01")
    modes = ("base_sharpe7", "no_pareto", "frontier_only", "pareto_le2", "dominated_tail", "pareto_le1")
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
        "evidence_class": "NEW_PREREGISTERED_PURE_CRYPTO_GEOMETRY",
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
                w = clean.sel(time=slice(start, end))
                d = data.sel(time=slice(None, end))
                stat = qnstats.calc_stat(d, w, slippage_factor=cost, points_per_year=365).sel(time=slice(start, end))
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
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--research", action="store_true")
    p.add_argument("--multipass", action="store_true")
    p.add_argument("--check-correlation", action="store_true")
    p.add_argument("--output", default=None)
    a = p.parse_args()
    if a.research:
        run_research(a.output)
    elif a.multipass:
        run_multipass(a.check_correlation)
    else:
        p.print_help()


if __name__ == "__main__":
    _main()
