"""Frontier-M volatility-slope dispersion opportunity state — IMPLEMENTED, UNMEASURED.

Experiment: frontier_20260912m_slope_dispersion_opportunity
Preregistration SHA256: 1a06b36543ef9a6987f674a474e362c2e974e17e676bc19ee1ac29e4fe8e7c20

Mechanism: deploy a residual-trend top-K book only while cross-sectional
short-vs-long residual-volatility slopes are unusually dispersed and expanding.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
EPS = 1e-12
TREND_DAYS = 21
FAMILY = "slope_dispersion_opportunity"
PARAMS = {"window": 63, "top_k": 5}
STATE_LAG = 7


def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)


def _base(data):
    close = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = _field(data, "is_liquid").eq(1) & close.notna()
    r = np.log(close / close.shift(1))
    market = r.where(liquid).sort_index(axis=1).mean(axis=1)
    residual = r.sub(market, axis=0)
    return close, liquid, residual


def _rv(residual, n):
    return residual.rolling(n, min_periods=max(5, n // 2)).std()


def _pct_rank(values, eligible):
    ordered = values.sort_index(axis=1)
    mask = eligible.reindex(columns=ordered.columns).fillna(False)
    ranks = ordered.where(mask).rank(axis=1, pct=True, method="first")
    return ranks.reindex(columns=values.columns)


def _rotate_eligible(values, eligible):
    ordered = values.sort_index(axis=1)
    mask = eligible.reindex(columns=ordered.columns).fillna(False)
    out = ordered.copy()
    for i in range(len(out)):
        arr = out.iloc[i].to_numpy(dtype=float).copy()
        loc = np.flatnonzero(mask.iloc[i].to_numpy(dtype=bool) & np.isfinite(arr))
        if len(loc) > 1:
            arr[loc] = np.roll(arr[loc], 1)
            out.iloc[i] = arr
    return out.reindex(columns=values.columns)


def _allocate(score, liquid, times, top_k):
    ranked = score.where(liquid & np.isfinite(score) & (score > 0)).sort_index(axis=1)
    selected = ranked.rank(axis=1, ascending=False, method="first") <= top_k
    selected = selected.reindex(columns=score.columns)
    target = selected.astype(float) * min(NAME_CAP, 1.0 / top_k)
    monday = pd.Series(pd.DatetimeIndex(times).dayofweek == 0, index=target.index)
    events = target.where(monday, axis=0).mask(~liquid, 0.0)
    weights = events.ffill(limit=6).fillna(0.0).where(liquid, 0.0)
    return xr.DataArray(weights.to_numpy(dtype=float), dims=("time", "asset"),
                        coords={"time": times, "asset": score.columns}, name=COMPETITION_TYPE)


def signals(data, window, mode="base"):
    _, liquid, residual = _base(data)
    short = max(7, window // 6)
    sv = _rv(residual, short)
    lv = _rv(residual, window)
    slope = np.log((sv + EPS) / (lv + EPS)).where(liquid)
    ordered = slope.sort_index(axis=1)
    dispersion = ordered.std(axis=1, ddof=0)
    baseline = dispersion.rolling(window, min_periods=max(14, window // 2)).median()
    change = dispersion - dispersion.shift(STATE_LAG)
    base_state = (dispersion > baseline) & (change > 0.0)
    low_state = (dispersion < baseline) & (change < 0.0)
    trend = residual.rolling(TREND_DAYS, min_periods=10).sum().clip(lower=0.0)
    if mode == "base":
        state = base_state
    elif mode == "ablation":
        state = pd.Series(True, index=trend.index)
    elif mode == "falsifier":
        state = low_state
    else:
        raise ValueError("unknown control mode")
    score = trend.where(state, 0.0)
    return score.replace([np.inf, -np.inf], np.nan), liquid


def strategy(data, params=None, mode="base"):
    p = dict(PARAMS if params is None else params)
    if set(p) != {"window", "top_k"} or any(type(v) is not int or v < 1 for v in p.values()):
        raise ValueError("expected positive integer window and top_k")
    if p["window"] not in {42, 63, 84} or p["top_k"] != 5:
        raise ValueError("outside preregistered Frontier-M grid")
    if 2 * p["window"] + TREND_DAYS + STATE_LAG + 14 >= LOOKBACK_DAYS:
        raise ValueError("parameters exceed finite replay horizon")
    if mode not in {"base", "ablation", "falsifier"}:
        raise ValueError("unknown mode")
    score, liquid = signals(data, p["window"], mode)
    return _allocate(score, liquid, data.time, p["top_k"])


def load_data(period):
    os.environ.setdefault("API_KEY", "default")
    import qnt.data as qndata
    return qndata.cryptodaily_load_data(tail=period)


if __name__ == "__main__":
    os.environ.setdefault("API_KEY", "default")
    import qnt.backtester as qnbt
    qnbt.backtest(competition_type=COMPETITION_TYPE, load_data=load_data,
                   lookback_period=LOOKBACK_DAYS, start_date="2016-01-01",
                   strategy=strategy, analyze=True, check_correlation=True)
