"""Frontier-N elasticity rank migration — IMPLEMENTED, UNMEASURED.

Experiment: frontier_20260913n_elasticity_rank_migration
Preregistration: experiments/frontier_20260913n/elasticity_rank_migration/preregistration.json

The signal compares bounded cross-sectional rank of positive range-normalized
price displacement with the rank of activity required to produce it, then trades
upward migration in that self-asset efficiency state under positive residual
trend. Only daily OHLCV + historical is_liquid are used.
"""
from __future__ import annotations

import os
import numpy as np
import pandas as pd
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
FAMILY = "elasticity_rank_migration"
PARAMS = {"window": 42, "top_k": 5}
MIGRATION_LAG = 21
TREND_DAYS = 21
SHARE_BASELINE_DAYS = 21


def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)


def _rotate_eligible(frame, eligible):
    ordered = frame.sort_index(axis=1)
    mask = eligible.reindex(columns=ordered.columns).fillna(False)
    out = ordered.copy()
    for i in range(len(out)):
        arr = out.iloc[i].to_numpy(dtype=float).copy()
        loc = np.flatnonzero(mask.iloc[i].to_numpy(dtype=bool) & np.isfinite(arr))
        if len(loc) > 1:
            arr[loc] = np.roll(arr[loc], 1)
        out.iloc[i] = arr
    return out.reindex(columns=frame.columns)


def _components(data):
    close = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    open_ = _field(data, "open").where(lambda x: np.isfinite(x) & (x > 0))
    high = _field(data, "high").where(lambda x: np.isfinite(x) & (x > 0))
    low = _field(data, "low").where(lambda x: np.isfinite(x) & (x > 0))
    vol = _field(data, "vol").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = _field(data, "is_liquid").eq(1) & close.notna() & open_.notna() & high.notna() & low.notna()

    ret = np.log(close / close.shift(1))
    market = ret.where(liquid).sort_index(axis=1).mean(axis=1)
    residual = ret.sub(market, axis=0).where(liquid)

    bar_range = (high - low).where((high - low) > 0)
    body = np.log(close / open_).replace([np.inf, -np.inf], np.nan)
    range_fraction = (bar_range / close.shift(1)).replace([np.inf, -np.inf], np.nan)
    positive_displacement = (body.clip(lower=0.0) / range_fraction.replace(0, np.nan)).clip(lower=0.0, upper=1.0)

    dollar = (close * vol).where(liquid)
    total = dollar.sort_index(axis=1).sum(axis=1, min_count=1).replace(0, np.nan)
    share = dollar.div(total, axis=0).where(lambda x: x > 0)
    baseline = share.rolling(SHARE_BASELINE_DAYS, min_periods=max(8, SHARE_BASELINE_DAYS // 2)).median()
    activity = np.log(share / baseline).replace([np.inf, -np.inf], np.nan).clip(lower=0.0)

    displacement_rank = positive_displacement.where(liquid).rank(axis=1, pct=True, method="average")
    activity_rank = activity.where(liquid).rank(axis=1, pct=True, method="average")
    efficiency = (displacement_rank - activity_rank).where(liquid)
    return efficiency, residual, liquid


def signals(data, window, mode="base"):
    efficiency, residual, liquid = _components(data)
    minp = max(10, window // 2)
    level = efficiency.rolling(window, min_periods=minp).mean()
    migration = level - level.shift(MIGRATION_LAG)
    trend = residual.rolling(TREND_DAYS, min_periods=max(8, TREND_DAYS // 2)).sum()

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
    if p["window"] not in {21, 42, 63} or p["top_k"] != 5:
        raise ValueError("outside preregistered Frontier-N grid")
    if p["window"] + MIGRATION_LAG + TREND_DAYS + SHARE_BASELINE_DAYS + 14 >= LOOKBACK_DAYS:
        raise ValueError("parameters exceed finite replay horizon")
    if mode not in {"base", "ablation", "falsifier"}:
        raise ValueError("unknown mode")
    times = pd.DatetimeIndex(data.time.values)
    if not times.is_unique or not times.is_monotonic_increasing:
        raise ValueError("times must be unique and increasing")
    if len(set(data.asset.values.tolist())) != data.sizes["asset"]:
        raise ValueError("assets must be unique")
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
