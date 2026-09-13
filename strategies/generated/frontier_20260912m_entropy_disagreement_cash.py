"""Frontier-M entropy disagreement cash gate — IMPLEMENTED, UNMEASURED.

Experiment: frontier_20260912m_entropy_disagreement_cash
Preregistration SHA256: 6df3b5736500bff180e1d9275d2eb79fdef05c345695d4dab6e30e9c1dd8320b

Mechanism: rank positive residual-trend names exactly as a simple trend book,
but deploy capital only when cross-sectional residual sequence-entropy
disagreement is high relative to prior Monday states. Pre-existing L reserve.
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
FAMILY = "entropy_disagreement_cash"
PARAMS = {"window": 84, "top_k": 5}
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
        if np.isfinite(block).all():
            patterns.append(tuple(np.argsort(block, kind="mergesort")))
    if len(patterns) < 8:
        return np.nan
    counts = np.array(list(Counter(patterns).values()), dtype=float)
    p = counts / counts.sum()
    return float(-np.sum(p * np.log(p)) / np.log(math.factorial(order)))

def _gate(disagreement, prior, mode):
    if mode == "ablation":
        return True
    if len(prior) == 0 or not np.isfinite(disagreement):
        return False
    threshold = float(np.nanmedian(np.asarray(prior, dtype=float)))
    if not np.isfinite(threshold):
        return False
    if mode == "base":
        return disagreement > threshold
    if mode == "falsifier":
        return disagreement < threshold
    raise ValueError("unknown mode")

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
    history = []
    history_len = max(4, window // 7)
    first = window + TREND_DAYS + 2

    for i in range(first, len(times)):
        if times[i].dayofweek != 0:
            continue
        cur = rs.iloc[i - window + 1:i + 1]
        entropy = pd.Series({a: _ordinal_entropy(cur[a].to_numpy()) for a in ordered})
        eligible = ls.iloc[i].astype(bool)
        valid = entropy.where(eligible).dropna()
        disagreement = float(valid.std(ddof=0)) if len(valid) >= 2 else np.nan
        prior = history[-history_len:]
        active = _gate(disagreement, prior, mode)
        trend = rs.iloc[i - TREND_DAYS + 1:i + 1].sum(min_count=max(5, TREND_DAYS // 2))
        if active:
            out.iloc[i] = trend.clip(lower=0.0).where(eligible, 0.0).fillna(0.0).reindex(ordered).to_numpy()
        if np.isfinite(disagreement):
            history.append(disagreement)

    return out.reindex(columns=close.columns), liquid


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


def strategy(data, params=None, mode="base"):
    p = dict(PARAMS if params is None else params)
    if set(p) != {"window", "top_k"} or any(type(v) is not int or v < 1 for v in p.values()):
        raise ValueError("expected positive integer window and top_k")
    if p["window"] not in {63, 84, 126} or p["top_k"] != 5:
        raise ValueError("outside preregistered Frontier-M grid")
    if p["window"] + TREND_DAYS + 14 >= LOOKBACK_DAYS:
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
