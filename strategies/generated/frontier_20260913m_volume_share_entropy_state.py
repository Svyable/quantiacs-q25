"""Frontier-M volume-share entropy state — activated from preexisting unmeasured reserve."""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
FAMILY = "volume_share_entropy_state"
PREREGISTRATION_SHA256 = "6dea6d241fa326dffff5d0b76401b1d55d070bb8e775fe951a9edf7e2ef159b4"
PARAMS = {"window": 42, "top_k": 5}
MIGRATION_LAG = 21
TREND_DAYS = 21

def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)

def signals(data, window, mode="base"):
    close = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    vol = _field(data, "vol").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = _field(data, "is_liquid").eq(1) & close.notna()
    r = np.log(close / close.shift(1))
    market = r.where(liquid).sort_index(axis=1).mean(axis=1)
    residual = r.sub(market, axis=0)
    dollar = (close * vol).where(liquid)
    total = dollar.sort_index(axis=1).sum(axis=1, min_count=1).replace(0, np.nan)
    share = dollar.div(total, axis=0)
    level = share.rolling(window, min_periods=max(10, window // 2)).mean()
    migration = level - level.shift(MIGRATION_LAG)
    p = share.clip(lower=1e-15)
    entropy = -(p * np.log(p)).sum(axis=1, min_count=2)
    n = liquid.sum(axis=1).clip(lower=2)
    entropy = entropy / np.log(n)
    concentration_change = entropy.shift(MIGRATION_LAG) - entropy
    if mode == "base":
        state = concentration_change.clip(lower=0.0)
    elif mode == "ablation":
        state = pd.Series(1.0, index=entropy.index)
    elif mode == "falsifier":
        state = (-concentration_change).clip(lower=0.0)
    else:
        raise ValueError("unknown control mode")
    trend = residual.rolling(TREND_DAYS, min_periods=10).sum()
    score = migration.clip(lower=0.0).mul(state, axis=0).where(liquid & (trend > 0), 0.0)
    return score.replace([np.inf, -np.inf], np.nan), liquid

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
    if p["window"] not in {21, 42, 63} or p["top_k"] != 5:
        raise ValueError("outside preregistered Frontier-M grid")
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
