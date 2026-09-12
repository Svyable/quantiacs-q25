"""Frontier-K nearest-peer detachment — IMPLEMENTED, UNMEASURED.

Preregistered before implementation at:
experiments/frontier_20260912k/nearest_peer_detachment/preregistration.json

Mechanism: when the residual market graph fragments, rank assets whose single
strongest residual peer weakened most while their own residual trend is positive.
No symbols are hand-picked; only daily Quantiacs OHLCV + historical is_liquid are used.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
FAMILY = "nearest_peer_detachment"
PARAMS = {"window": 63, "top_k": 5}
GRAPH_LAG = 21
TREND_DAYS = 21


def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)


def _residual_corr(frame, min_periods):
    corr = frame.corr(min_periods=min_periods).replace([np.inf, -np.inf], np.nan)
    if corr.empty:
        return corr, np.nan
    values = corr.to_numpy(dtype=float).copy()
    np.fill_diagonal(values, np.nan)
    global_level = float(np.nanmean(np.abs(values))) if np.isfinite(values).any() else np.nan
    return corr, global_level


def _strongest_abs_peer(corr):
    values = np.abs(corr.to_numpy(dtype=float)).copy()
    if values.size == 0:
        return pd.Series(dtype=float)
    np.fill_diagonal(values, np.nan)
    finite = np.isfinite(values)
    strongest = np.where(finite.any(axis=1), np.nanmax(values, axis=1), np.nan)
    return pd.Series(strongest, index=corr.index)


def signals(data, window, mode="base"):
    close = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = _field(data, "is_liquid").eq(1) & close.notna()
    returns = np.log(close / close.shift(1))
    market = returns.where(liquid).mean(axis=1)
    residual = returns.sub(market, axis=0)

    ordered = sorted(close.columns)
    residual_s = residual.reindex(columns=ordered)
    out = pd.DataFrame(0.0, index=close.index, columns=ordered)
    times = pd.DatetimeIndex(close.index)
    minp = max(16, window // 2)
    first = window + GRAPH_LAG + TREND_DAYS + 2

    for i in range(first, len(times)):
        if times[i].dayofweek != 0:
            continue
        cur = residual_s.iloc[i - window + 1:i + 1]
        prev_end = i - GRAPH_LAG
        prev = residual_s.iloc[prev_end - window + 1:prev_end + 1]
        cur_corr, cur_global = _residual_corr(cur, minp)
        prev_corr, prev_global = _residual_corr(prev, minp)
        if not np.isfinite(cur_global) or not np.isfinite(prev_global):
            continue

        fragmentation = max(prev_global - cur_global, 0.0)
        if fragmentation <= 0:
            continue
        cur_peer = _strongest_abs_peer(cur_corr)
        prev_peer = _strongest_abs_peer(prev_corr)
        detachment = (prev_peer - cur_peer).replace([np.inf, -np.inf], np.nan)
        trend = residual_s.iloc[i - TREND_DAYS + 1:i + 1].sum(
            min_count=max(5, TREND_DAYS // 2)
        )

        if mode == "base":
            node = detachment
        elif mode == "ablation":
            node = (1.0 - cur_peer).clip(lower=0.0)
        elif mode == "falsifier":
            vals = detachment.to_numpy(dtype=float)
            node = pd.Series(np.roll(vals, 1), index=detachment.index)
        else:
            raise ValueError("unknown control mode")

        raw = node.clip(lower=0.0) * fragmentation
        raw = raw.where(trend > 0, 0.0)
        out.iloc[i] = raw.reindex(ordered).fillna(0.0).to_numpy()

    return out.reindex(columns=close.columns), liquid


def _allocate(score, liquid, times, top_k):
    ranked = score.where(liquid & (score > 0)).sort_index(axis=1)
    selected = ranked.rank(axis=1, ascending=False, method="first") <= top_k
    selected = selected.reindex(columns=score.columns)
    raw = selected.astype(float) * min(NAME_CAP, 1.0 / top_k)
    monday = pd.Series(pd.DatetimeIndex(times).dayofweek == 0, index=raw.index)
    weights = raw.where(monday, axis=0).ffill(limit=6).fillna(0.0)
    weights = weights.where(liquid, 0.0)
    return xr.DataArray(
        weights.to_numpy(dtype=float),
        dims=("time", "asset"),
        coords={"time": times, "asset": score.columns},
        name=COMPETITION_TYPE,
    )


def strategy(data, params=None, mode="base"):
    p = dict(PARAMS if params is None else params)
    if set(p) != {"window", "top_k"}:
        raise ValueError("expected exactly window, top_k")
    if any(type(v) is not int or v < 1 for v in p.values()):
        raise ValueError("parameters must be positive integers")
    if p["window"] not in {42, 63, 84} or p["top_k"] != 5:
        raise ValueError("outside preregistered Frontier-K grid")
    if p["window"] + GRAPH_LAG + TREND_DAYS + 14 >= LOOKBACK_DAYS:
        raise ValueError("parameters exceed finite replay horizon")
    if mode not in {"base", "ablation", "falsifier"}:
        raise ValueError("unknown control mode")
    times = pd.DatetimeIndex(data.time.values)
    if not times.is_unique or not times.is_monotonic_increasing:
        raise ValueError("times must be unique and increasing")
    if len(set(data.asset.values.tolist())) != data.sizes["asset"]:
        raise ValueError("assets must be unique")
    score, liquid = signals(data, p["window"], mode)
    return _allocate(score, liquid, data.time, p["top_k"])


def load_data(period):
    import qnt.data as qndata
    return qndata.cryptodaily_load_data(tail=period)


if __name__ == "__main__":
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
