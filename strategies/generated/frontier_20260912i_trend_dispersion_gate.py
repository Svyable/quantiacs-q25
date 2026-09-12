"""PENDING RESEARCH STRATEGY — frontier_20260912i_trend_dispersion_gate.
Experiment: frontier_20260912i_trend_dispersion_gate
Preregistration SHA256: 062ab46bc0a8be30198dce08d46a5625d5893544b6d309cfa844fec1cd7df35b
Mechanism: cross-sectional residual-trend opportunity density.
No performance or submission claim.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
PARAMS = {"window": 63, "top_k": 5}
TREND_DAYS = 21


def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)


def _context(data):
    close = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = _field(data, "is_liquid").eq(1) & close.notna()
    returns = np.log(close / close.shift(1))
    market = returns.where(liquid).sort_index(axis=1).mean(axis=1)
    return close, liquid, returns.sub(market, axis=0)


def signals(data, window, mode="base"):
    close, liquid, residual = _context(data)
    trend = residual.rolling(TREND_DAYS, min_periods=max(5, TREND_DAYS // 2)).sum()
    positive = trend.clip(lower=0.0)
    rank = positive.where(liquid).rank(axis=1, pct=True, method="average").fillna(0.0)
    dispersion = trend.where(liquid).std(axis=1)
    baseline = dispersion.rolling(window, min_periods=max(16, window // 2)).median().shift(1)
    expansion = (dispersion / (baseline + 1e-12) - 1.0).clip(lower=0.0)
    compression = (baseline / (dispersion + 1e-12) - 1.0).clip(lower=0.0)
    if mode == "base":
        gate = expansion.clip(upper=1.0)
    elif mode == "ablation":
        gate = pd.Series(1.0, index=trend.index)
    elif mode == "falsifier":
        gate = compression.clip(upper=1.0)
    else:
        raise ValueError("unknown mode")
    score = rank.mul(gate.fillna(0.0), axis=0).where(positive > 0, 0.0)
    return score, liquid


def _allocate(score, liquid, times, top_k):
    ranked = score.where(liquid & np.isfinite(score) & (score > 0)).sort_index(axis=1)
    selected = ranked.rank(axis=1, ascending=False, method="first") <= top_k
    target = selected.reindex(columns=score.columns).astype(float) * min(NAME_CAP, 1 / top_k)
    monday = pd.Series(pd.DatetimeIndex(times).dayofweek == 0, index=target.index)
    events = target.where(monday, axis=0).mask(~liquid, 0.0)
    weights = events.ffill(limit=6).fillna(0.0).where(liquid, 0.0)
    return xr.DataArray(weights.to_numpy(dtype=float), dims=("time", "asset"), coords={"time": pd.DatetimeIndex(times), "asset": score.columns}, name=COMPETITION_TYPE)


def strategy(data, params=None, mode="base"):
    p = dict(PARAMS if params is None else params)
    if set(p) != {"window", "top_k"} or any(type(v) is not int or v < 1 for v in p.values()):
        raise ValueError("expected positive integer window and top_k")
    if p["window"] + TREND_DAYS + 40 >= LOOKBACK_DAYS:
        raise ValueError("parameters exceed bounded replay horizon")
    if mode not in {"base", "ablation", "falsifier"}:
        raise ValueError("unknown mode")
    times = pd.DatetimeIndex(data.time.values)
    if not times.is_unique or not times.is_monotonic_increasing or len(times) == 0:
        raise ValueError("nonempty increasing unique dates required")
    if len(set(data.asset.values.tolist())) != data.sizes["asset"]:
        raise ValueError("unique asset coordinates required")
    score, liquid = signals(data, p["window"], mode)
    return _allocate(score, liquid, data.time, p["top_k"])


def load_data(period):
    os.environ.setdefault("API_KEY", "default")
    import qnt.data as qndata
    return qndata.cryptodaily_load_data(tail=period)


if __name__ == "__main__":
    os.environ.setdefault("API_KEY", "default")
    import qnt.backtester as qnbt
    qnbt.backtest(competition_type=COMPETITION_TYPE, load_data=load_data, lookback_period=LOOKBACK_DAYS, start_date="2016-01-01", strategy=strategy, analyze=True, check_correlation=True)
