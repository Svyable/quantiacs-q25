"""Frontier-L permutation entropy contraction — IMPLEMENTED, UNMEASURED.

Experiment: frontier_20260912l_permutation_entropy_contraction
Preregistration SHA256: d9554ac8335e568e6a6503d4bdb5eb423c29c007e466f40d3fd1502a50df7c18

Mechanism: falling ordinal-pattern entropy of residual returns, conditional on
positive residual trend. This uses sequence structure rather than volatility,
plain sign hit-rate, or raw trend strength.
"""
from __future__ import annotations
import os
from collections import Counter
import math
import numpy as np
import pandas as pd
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
FAMILY = "permutation_entropy_contraction"
PARAMS = {"window": 84, "top_k": 5}
ENTROPY_LAG = 21
TREND_DAYS = 21
ORDER = 3


def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)


def _ordinal_entropy(values, order=ORDER):
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if len(arr) < max(12, order * 4):
        return np.nan
    patterns = []
    for i in range(len(arr) - order + 1):
        block = arr[i:i + order]
        if not np.isfinite(block).all():
            continue
        patterns.append(tuple(np.argsort(block, kind="mergesort")))
    if len(patterns) < 8:
        return np.nan
    counts = np.array(list(Counter(patterns).values()), dtype=float)
    p = counts / counts.sum()
    entropy = -np.sum(p * np.log(p))
    return float(entropy / np.log(math.factorial(order)))


def _rotate_eligible(values, eligible):
    ordered = values.sort_index()
    mask = eligible.reindex(ordered.index).fillna(False).to_numpy(dtype=bool)
    arr = ordered.to_numpy(dtype=float).copy()
    loc = np.flatnonzero(mask & np.isfinite(arr))
    if len(loc) > 1:
        arr[loc] = np.roll(arr[loc], 1)
    return pd.Series(arr, index=ordered.index).reindex(values.index)


def signals(data, window, mode="base"):
    close = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = _field(data, "is_liquid").eq(1) & close.notna()
    r = np.log(close / close.shift(1))
    market = r.where(liquid).sort_index(axis=1).mean(axis=1)
    residual = r.sub(market, axis=0).where(liquid)
    ordered = sorted(close.columns)
    rs = residual.reindex(columns=ordered)
    ls = liquid.reindex(columns=ordered)
    out = pd.DataFrame(0.0, index=close.index, columns=ordered)
    times = pd.DatetimeIndex(close.index)
    first = window + ENTROPY_LAG + TREND_DAYS + 2
    for i in range(first, len(times)):
        if times[i].dayofweek != 0:
            continue
        cur = rs.iloc[i - window + 1:i + 1]
        prev_end = i - ENTROPY_LAG
        prev = rs.iloc[prev_end - window + 1:prev_end + 1]
        cur_e = pd.Series({a: _ordinal_entropy(cur[a].to_numpy()) for a in ordered})
        prev_e = pd.Series({a: _ordinal_entropy(prev[a].to_numpy()) for a in ordered})
        contraction = (prev_e - cur_e).replace([np.inf, -np.inf], np.nan)
        trend = rs.iloc[i - TREND_DAYS + 1:i + 1].sum(min_count=max(5, TREND_DAYS // 2))
        eligible = ls.iloc[i].astype(bool)
        if mode == "base":
            node = contraction.clip(lower=0.0)
        elif mode == "ablation":
            node = (1.0 - cur_e).clip(lower=0.0)
        elif mode == "falsifier":
            node = _rotate_eligible(contraction, eligible).clip(lower=0.0)
        else:
            raise ValueError("unknown control mode")
        score = node.where(eligible & (trend > 0), 0.0)
        out.iloc[i] = score.reindex(ordered).fillna(0.0).to_numpy()
    return out.reindex(columns=close.columns), liquid


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


def strategy(data, params=None, mode="base"):
    p = dict(PARAMS if params is None else params)
    if set(p) != {"window", "top_k"} or any(type(v) is not int or v < 1 for v in p.values()):
        raise ValueError("expected positive integer window and top_k")
    if p["window"] not in {63, 84, 126} or p["top_k"] != 5:
        raise ValueError("outside preregistered Frontier-L grid")
    if p["window"] + ENTROPY_LAG + TREND_DAYS + 14 >= LOOKBACK_DAYS:
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
