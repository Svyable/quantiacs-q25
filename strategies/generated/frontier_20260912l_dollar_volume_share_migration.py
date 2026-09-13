"""Frontier-L dollar-volume share migration — IMPLEMENTED, UNMEASURED.

Experiment: frontier_20260912l_dollar_volume_share_migration
Preregistration SHA256: b6abb0d28b86db9d73f8a64170e70b5535f59a2357b4c43c557db6e3e761219f

Mechanism: rising share of eligible-universe dollar volume, conditional on
positive residual trend. The primitive is cross-sectional activity share, not
raw abnormal volume and not a directed volume-return network.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
FAMILY = "dollar_volume_share_migration"
PARAMS = {"window": 42, "top_k": 5}
MIGRATION_LAG = 21
TREND_DAYS = 21


def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)


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
    trend = residual.rolling(TREND_DAYS, min_periods=max(5, TREND_DAYS // 2)).sum()
    if mode == "base":
        node = migration
    elif mode == "ablation":
        node = level
    elif mode == "falsifier":
        node = _rotate_eligible(migration, liquid)
    else:
        raise ValueError("unknown control mode")
    score = node.clip(lower=0.0).where(liquid & (trend > 0), 0.0)
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


def strategy(data, params=None, mode="base"):
    p = dict(PARAMS if params is None else params)
    if set(p) != {"window", "top_k"} or any(type(v) is not int or v < 1 for v in p.values()):
        raise ValueError("expected positive integer window and top_k")
    if p["window"] not in {21, 42, 63} or p["top_k"] != 5:
        raise ValueError("outside preregistered Frontier-L grid")
    if p["window"] + MIGRATION_LAG + TREND_DAYS + 14 >= LOOKBACK_DAYS:
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
