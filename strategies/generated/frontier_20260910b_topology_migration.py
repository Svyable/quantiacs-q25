"""frontier_20260910b_topology_migration — PENDING RESEARCH STRATEGY; no performance or submission claim.
Experiment: frontier_20260910b_topology_migration
Preregistration SHA256: bd61d69cd3859ee459162755259281e1fc9b741e8a4a6e2624e49c98a4b660d4
Mechanism: residual correlation-topology centrality migration during fragmentation
Nearest incumbent: C165 / residual-dispersion and V10 residual-momentum families
Novelty axes: information_primitive, transform, timing_or_state_condition

Completed daily Quantiacs OHLCV + historical is_liquid only. The evaluator applies
the execution lag. All signal state is reconstructable from <=365 daily observations.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
FAMILY = "topology_migration"
PARAMS = {"window": 63, "top_k": 5}
GRAPH_LAG = 21
TREND_DAYS = 21


def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)


def _centrality(frame, min_periods):
    corr = frame.corr(min_periods=min_periods)
    values = corr.to_numpy(dtype=float)
    if values.size == 0:
        return pd.Series(dtype=float), np.nan
    np.fill_diagonal(values, np.nan)
    central = np.nanmean(np.abs(values), axis=1)
    global_level = float(np.nanmean(np.abs(values))) if np.isfinite(values).any() else np.nan
    return pd.Series(central, index=corr.index), global_level


def signals(data, window, mode="base"):
    c = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = _field(data, "is_liquid").eq(1) & c.notna()
    r = np.log(c / c.shift(1))
    market = r.where(liquid).mean(axis=1)
    residual = r.sub(market, axis=0)

    ordered = sorted(c.columns)
    residual_s = residual.reindex(columns=ordered)
    out = pd.DataFrame(0.0, index=c.index, columns=ordered)
    times = pd.DatetimeIndex(c.index)
    minp = max(16, window // 2)
    first = window + GRAPH_LAG + 2

    for i in range(first, len(times)):
        if times[i].dayofweek != 0:
            continue
        cur = residual_s.iloc[i - window + 1:i + 1]
        prev_end = i - GRAPH_LAG
        prev = residual_s.iloc[prev_end - window + 1:prev_end + 1]
        cur_cent, cur_global = _centrality(cur, minp)
        prev_cent, prev_global = _centrality(prev, minp)
        if not np.isfinite(cur_global) or not np.isfinite(prev_global):
            continue
        fragmentation = max(prev_global - cur_global, 0.0)
        if fragmentation <= 0:
            continue
        migration = (prev_cent - cur_cent).replace([np.inf, -np.inf], np.nan)
        trend = residual_s.iloc[max(0, i - TREND_DAYS + 1):i + 1].sum(min_count=max(5, TREND_DAYS // 2))

        if mode == "ablation":
            node = (1.0 - cur_cent).clip(lower=0.0)
        elif mode == "falsifier":
            vals = migration.to_numpy(dtype=float)
            node = pd.Series(np.roll(vals, 1), index=migration.index)
        elif mode == "base":
            node = migration
        else:
            raise ValueError("unknown control mode")

        raw = node.clip(lower=0.0) * fragmentation
        raw = raw.where(trend > 0, 0.0)
        out.iloc[i] = raw.reindex(ordered).fillna(0.0).to_numpy()

    return out.reindex(columns=c.columns), liquid


def strategy(data, params=None, mode="base"):
    p = dict(PARAMS if params is None else params)
    if set(p) != {"window", "top_k"}:
        raise ValueError("expected exactly window, top_k")
    if any(type(v) is not int or v < 1 for v in p.values()):
        raise ValueError("parameters must be positive integers")
    if 2 * p["window"] + GRAPH_LAG + TREND_DAYS + 14 >= LOOKBACK_DAYS:
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

def _allocate(score, liquid, times, top_k):
    ranked = score.where(liquid & (score > 0)).sort_index(axis=1)
    selected = ranked.rank(axis=1, ascending=False, method="first") <= top_k
    selected = selected.reindex(columns=score.columns)
    raw = selected.astype(float) * min(NAME_CAP, 1 / top_k)
    monday = pd.Series(pd.DatetimeIndex(times).dayofweek == 0, index=raw.index)
    weights = raw.where(monday, axis=0).ffill(limit=6).fillna(0.0)
    weights = weights.where(liquid, 0.0)
    return xr.DataArray(
        weights.to_numpy(dtype=float),
        dims=("time", "asset"),
        coords={"time": times, "asset": score.columns},
        name=COMPETITION_TYPE,
    )


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
