"""Frontier-M entropy disagreement cash gate — activated from preexisting unmeasured reserve."""
from __future__ import annotations
import os, math
from collections import Counter
import numpy as np
import pandas as pd
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
FAMILY = "entropy_disagreement_cash"
PREREGISTRATION_SHA256 = "0099277375cd53423468d150e39c1fe8871a8afb968e9c3960b8d67ad2f23429"
PARAMS = {"window": 84, "top_k": 5}
TREND_DAYS = 21
ORDER = 3
STATE_BASELINE = 42

def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)

def _ordinal_entropy(values):
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if len(arr) < 12:
        return np.nan
    patterns = [tuple(np.argsort(arr[i:i+ORDER], kind="mergesort")) for i in range(len(arr)-ORDER+1)]
    if len(patterns) < 8:
        return np.nan
    counts = np.array(list(Counter(patterns).values()), dtype=float)
    p = counts / counts.sum()
    return float(-(p * np.log(p)).sum() / np.log(math.factorial(ORDER)))

def signals(data, window, mode="base"):
    close = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = _field(data, "is_liquid").eq(1) & close.notna()
    r = np.log(close / close.shift(1))
    market = r.where(liquid).sort_index(axis=1).mean(axis=1)
    residual = r.sub(market, axis=0).where(liquid)
    ordered = sorted(close.columns)
    rs = residual.reindex(columns=ordered)
    ls = liquid.reindex(columns=ordered)
    raw = pd.DataFrame(0.0, index=close.index, columns=ordered)
    disagreement = pd.Series(np.nan, index=close.index, dtype=float)
    times = pd.DatetimeIndex(close.index)
    for i in range(window + TREND_DAYS, len(times)):
        if times[i].dayofweek != 0:
            continue
        ent = pd.Series({a:_ordinal_entropy(rs[a].iloc[i-window+1:i+1].to_numpy()) for a in ordered})
        eligible = ls.iloc[i].astype(bool)
        vals = ent.where(eligible).dropna()
        if len(vals) < 3:
            continue
        disagreement.iloc[i] = float(vals.std(ddof=0))
        trend = rs.iloc[i-TREND_DAYS+1:i+1].sum(min_count=10)
        raw.iloc[i] = trend.clip(lower=0.0).where(eligible, 0.0).fillna(0.0).to_numpy()
    baseline = disagreement.ffill().rolling(STATE_BASELINE, min_periods=12).median()
    high = (disagreement > baseline).fillna(False)
    low = (disagreement < baseline).fillna(False)
    if mode == "base":
        gate = high
    elif mode == "ablation":
        gate = pd.Series(True, index=raw.index)
    elif mode == "falsifier":
        gate = low
    else:
        raise ValueError("unknown control mode")
    score = raw.mul(gate.astype(float), axis=0)
    return score.reindex(columns=close.columns), liquid

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

def load_data(period):
    os.environ.setdefault("API_KEY", "default")
    import qnt.data as qndata
    return qndata.cryptodaily_load_data(tail=period)

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

if __name__ == "__main__":
    os.environ.setdefault("API_KEY", "default")
    import qnt.backtester as qnbt
    qnbt.backtest(competition_type=COMPETITION_TYPE, load_data=load_data,
                   lookback_period=LOOKBACK_DAYS, start_date="2016-01-01",
                   strategy=strategy, analyze=True, check_correlation=True)
