"""Frontier-N directional elasticity asymmetry — IMPLEMENTED, UNMEASURED.

Experiment: frontier_20260913n_directional_elasticity_asymmetry
Preregistration: experiments/frontier_20260913n/directional_elasticity_asymmetry/preregistration.json
Preregistration SHA256: af6830832a7e2bfb563075a3789a27250be17a7145782264a98c13630a6e2339

The signal asks whether positive daily bars reprice more efficiently than
negative bars after discounting by relative activity. It is a self-asset daily
bar geometry object, not a directed return/volume network. Only completed OHLCV
and historical is_liquid are used.
"""
from __future__ import annotations

import os
import numpy as np
import pandas as pd
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
FAMILY = "directional_elasticity_asymmetry"
PARAMS = {"window": 63, "top_k": 5}
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

    body = np.log(close / open_).replace([np.inf, -np.inf], np.nan)
    bar_range = (high - low).where((high - low) > 0)
    range_fraction = (bar_range / close.shift(1)).replace([np.inf, -np.inf], np.nan)
    displacement_efficiency = (body.abs() / range_fraction.replace(0, np.nan)).clip(lower=0.0, upper=1.0)

    dollar = (close * vol).where(liquid)
    total = dollar.sort_index(axis=1).sum(axis=1, min_count=1).replace(0, np.nan)
    share = dollar.div(total, axis=0).where(lambda x: x > 0)
    baseline = share.rolling(SHARE_BASELINE_DAYS, min_periods=max(8, SHARE_BASELINE_DAYS // 2)).median()
    surprise = np.log(share / baseline).replace([np.inf, -np.inf], np.nan).clip(lower=0.0)
    activity_discount = 1.0 / (1.0 + surprise)
    efficiency = (displacement_efficiency * activity_discount).where(liquid)
    return efficiency, body, residual, liquid


def signals(data, window, mode="base"):
    efficiency, body, residual, liquid = _components(data)
    min_directional = max(8, window // 4)
    upside = efficiency.where(body > 0).rolling(window, min_periods=min_directional).mean()
    downside = efficiency.where(body < 0).rolling(window, min_periods=min_directional).mean()
    asymmetry = upside - downside
    trend = residual.rolling(TREND_DAYS, min_periods=max(8, TREND_DAYS // 2)).sum()

    if mode == "base":
        node = asymmetry
    elif mode == "ablation":
        node = upside
    elif mode == "falsifier":
        node = _rotate_eligible(asymmetry, liquid)
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
    if p["window"] not in {42, 63, 84} or p["top_k"] != 5:
        raise ValueError("outside preregistered Frontier-N grid")
    if p["window"] + TREND_DAYS + SHARE_BASELINE_DAYS + 14 >= LOOKBACK_DAYS:
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
