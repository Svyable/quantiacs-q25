"""Frozen forced-union Pareto strategy; experiment forced_union_20260922.

Automatic, symbol-agnostic, long-only strategy using only crypto_daily_long close
and historical is_liquid. Parameters are frozen in the preregistration.
"""
from __future__ import annotations

import numpy as np
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
STRATEGY_ID = "q25_forced_union_v1"
EXPERIMENT_ID = "forced_union_20260922"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
EPS = 1e-12


def _canonical(x):
    return np.sort(np.asarray(x.asset.values).astype(str))


def _close_liquid(data):
    close = data.sel(field="close").transpose("time", "asset").astype(float)
    z = data.sel(field="is_liquid").transpose("time", "asset")
    liquid = xr.where((z == 1) & np.isfinite(close) & (close > 0), 1.0, 0.0)
    return close, liquid


def _roll(x, n, m, op):
    if x.sizes["time"] < m:
        return xr.full_like(x, np.nan, dtype=float)
    width = min(n, x.sizes["time"])
    w = x.rolling(time=width).construct("_window")
    enough = w.count("_window") >= m
    if op == "mean":
        return w.mean("_window", skipna=True).where(enough)
    if op == "std":
        return w.std("_window", skipna=True, ddof=0).where(enough)
    raise ValueError(op)


def _mean_cs(x, liquid):
    a = _canonical(x)
    x, liquid = x.sel(asset=a), liquid.sel(asset=a)
    safe = xr.where(np.isfinite(x), x, 0.0)
    n = liquid.sum("asset")
    return xr.where(n > 0, (safe * liquid).sum("asset") / n, 0.0)


def _std_cs(x, liquid):
    a = _canonical(x)
    x, liquid = x.sel(asset=a), liquid.sel(asset=a)
    mean = _mean_cs(x, liquid)
    safe = xr.where(np.isfinite(x), x, 0.0)
    n = liquid.sum("asset")
    var = xr.where(n > 0, (((safe - mean) ** 2) * liquid).sum("asset") / n, 0.0)
    return np.sqrt(xr.where(var > 0, var, 0.0))


def _panel(close, liquid, scale):
    r = xr.where(np.isfinite(close / close.shift(time=1) - 1), close / close.shift(time=1) - 1, 0.0)
    mu = _roll(r, 7 * scale, 5 * scale, "mean")
    vol = _roll(r, 14 * scale, 7 * scale, "std")
    sharpe = np.sqrt(365.0) * mu / (vol + EPS)
    fast = _roll(close, 12 * scale, 8 * scale, "mean")
    slow = _roll(close, 48 * scale, 24 * scale, "mean")
    trend = fast / (slow + EPS) - 1.0
    momentum = close / close.shift(time=14 * scale) - 1.0
    peak = close.rolling(time=min(30 * scale, close.sizes["time"]), min_periods=15 * scale).max()
    drawdown = close / (peak + EPS) - 1.0
    valid = liquid * xr.where(np.isfinite(sharpe) & np.isfinite(vol) & np.isfinite(trend) & np.isfinite(momentum) & np.isfinite(drawdown), 1.0, 0.0)
    return sharpe, vol, trend, momentum, drawdown, valid


def _dominators(liquid, panel):
    sharpe, vol, trend, momentum, drawdown, _ = panel
    original = liquid.asset.values
    a = _canonical(liquid)
    lo = liquid.sel(asset=a)
    vals = xr.concat([sharpe.sel(asset=a), trend.sel(asset=a), momentum.sel(asset=a), drawdown.sel(asset=a), -vol.sel(asset=a)], dim="feature").transpose("time", "asset", "feature").values.astype(float)
    valid = (lo.values > 0) & np.isfinite(vals).all(axis=2)
    left, right = vals[:, :, None, :], vals[:, None, :, :]
    dominates = (left >= right).all(axis=3) & (left > right).any(axis=3)
    dominates &= valid[:, :, None] & valid[:, None, :]
    counts = dominates.sum(axis=1).astype(float)
    return xr.DataArray(counts, dims=("time", "asset"), coords={"time": lo.time.values, "asset": a}).sel(asset=original)


def _allocate(raw, liquid):
    original = raw.asset.values
    a = _canonical(raw)
    raw, liquid = raw.sel(asset=a), liquid.sel(asset=a)
    raw = xr.where(np.isfinite(raw) & (raw > 0), raw, 0.0) * liquid
    gross = raw.sum("asset")
    w = xr.where(gross > EPS, raw / gross, 0.0)
    w = xr.where(w > NAME_CAP, NAME_CAP, w) * liquid
    return w.sel(asset=original).transpose("time", "asset").fillna(0.0).reset_coords("field", drop=True)


def calculate_weights(data):
    close, liquid = _close_liquid(data)
    fast = _panel(close, liquid, 1)
    slow = _panel(close, liquid, 2)
    fast_counts = _dominators(liquid, fast)
    slow_counts = _dominators(liquid, slow)
    sharpe, vol, trend, momentum, drawdown, valid = fast
    mean_s = _mean_cs(sharpe, liquid)
    sd_s = _std_cs(sharpe, liquid)
    root = (trend > 0) & (momentum > 0) & (drawdown > -0.22) & (vol > 0) & (sharpe > mean_s) & (valid > 0) & (slow[5] > 0)
    # Frozen mechanism: union of fast and exactly doubled-horizon <=1-dominator skylines.
    join = (root & (fast_counts <= 1.0)) | (root & (slow_counts <= 1.0))
    quality = xr.where(sharpe > mean_s, (sharpe - mean_s + 0.10 * sd_s).clip(min=0.0), 0.0)
    score = xr.where(np.isfinite((quality ** 1.20) / (vol + 0.015)), (quality ** 1.20) / (vol + 0.015), 0.0) * liquid
    raw = _roll(score * join.astype(float), 3, 1, "mean") * liquid
    return _allocate(raw, liquid)


def strategy(data):
    return calculate_weights(data)


def load_data(period):
    import qnt.data as qndata
    return qndata.cryptodaily_load_data(tail=max(int(period), LOOKBACK_DAYS))
