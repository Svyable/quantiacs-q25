"""Frontier-N online AR surprise persistence — IMPLEMENTED, UNMEASURED.

Experiment: frontier_20260912n_online_ar_surprise_persistence
Preregistration SHA256: a29d5e42055f5af420178bf6dd924453a48561bf25c349cfd68662b962d0b062

Mechanism: rank persistent positive forecast errors from a tiny causal rolling
AR(1) model of market-residual return, rather than raw residual momentum.
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
SURPRISE_SCALE_DAYS = 21
PERSIST_DAYS = 5
MIN_POSITIVE_DAYS = 3
FAMILY = "online_ar_surprise_persistence"
PARAMS = {"window": 84, "top_k": 5}


def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)


def _base(data):
    close = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = _field(data, "is_liquid").eq(1) & close.notna()
    returns = np.log(close / close.shift(1))
    market = returns.where(liquid).sort_index(axis=1).mean(axis=1)
    residual = returns.sub(market, axis=0)
    return liquid, residual


def _online_ar1_surprise(residual, window):
    """One-step AR(1) innovation using coefficients estimated only through t-1."""
    x = residual.shift(1)
    y = residual
    min_periods = max(20, window // 2)

    mean_x = x.rolling(window, min_periods=min_periods).mean().shift(1)
    mean_y = y.rolling(window, min_periods=min_periods).mean().shift(1)
    mean_xy = (x * y).rolling(window, min_periods=min_periods).mean().shift(1)
    mean_x2 = (x * x).rolling(window, min_periods=min_periods).mean().shift(1)

    cov_xy = mean_xy - mean_x * mean_y
    var_x = (mean_x2 - mean_x * mean_x).clip(lower=0.0)
    phi = (cov_xy / (var_x + EPS)).clip(lower=-0.75, upper=0.75)
    alpha = mean_y - phi * mean_x
    forecast = alpha + phi * x
    return y - forecast


def _standardize(values):
    scale = values.rolling(SURPRISE_SCALE_DAYS, min_periods=10).std().shift(1)
    return values / (scale + EPS)


def _persistent_positive(z):
    positive_days = z.gt(0.0).rolling(PERSIST_DAYS, min_periods=PERSIST_DAYS).sum()
    total = z.rolling(PERSIST_DAYS, min_periods=PERSIST_DAYS).sum()
    return total.where(positive_days >= MIN_POSITIVE_DAYS).clip(lower=0.0)


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

    return xr.DataArray(
        weights.to_numpy(dtype=float),
        dims=("time", "asset"),
        coords={"time": times, "asset": score.columns},
        name=COMPETITION_TYPE,
    )


def signals(data, window, mode="base"):
    liquid, residual = _base(data)
    surprise = _online_ar1_surprise(residual, window)

    if mode == "base":
        z = _standardize(surprise)
    elif mode == "ablation":
        z = _standardize(residual)
    elif mode == "falsifier":
        z = _rotate_eligible(_standardize(surprise), liquid)
    else:
        raise ValueError("unknown control mode")

    score = _persistent_positive(z)
    return score.replace([np.inf, -np.inf], np.nan), liquid


def strategy(data, params=None, mode="base"):
    p = dict(PARAMS if params is None else params)
    if set(p) != {"window", "top_k"} or any(type(v) is not int or v < 1 for v in p.values()):
        raise ValueError("expected positive integer window and top_k")
    if p["window"] not in {63, 84, 126} or p["top_k"] != 5:
        raise ValueError("outside preregistered Frontier-N grid")
    if p["window"] + SURPRISE_SCALE_DAYS + PERSIST_DAYS + 14 >= LOOKBACK_DAYS:
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

    qnbt.backtest(
        competition_type=COMPETITION_TYPE,
        load_data=load_data,
        lookback_period=LOOKBACK_DAYS,
        start_date="2016-01-01",
        strategy=strategy,
        analyze=True,
        check_correlation=True,
    )
