"""PENDING RESEARCH STRATEGY — frontier_20260912j_positive_edge_shedding.
Experiment: frontier_20260912j_positive_edge_shedding
Preregistration SHA256: 8077cf9710d03fc56e11387cd929a72c5ec71d53b2c0337b0be8692bf6766b11
Mechanism: positive residual-edge shedding during fragmentation.
No performance or submission claim.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
PARAMS = {"window": 63, "top_k": 5}
GRAPH_LAG = 21
TREND_DAYS = 21

def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)

def _context(data):
    close = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = _field(data, "is_liquid").eq(1) & close.notna()
    returns = np.log(close / close.shift(1))
    market = returns.where(liquid).sort_index(axis=1).mean(axis=1)
    residual = returns.sub(market, axis=0).where(liquid)
    return close, liquid, residual

def _positive_stats(corr, labels):
    m = np.asarray(corr, dtype=float).copy()
    if m.shape[0] != len(labels):
        raise ValueError("label/matrix mismatch")
    np.fill_diagonal(m, np.nan)
    pos = np.where(np.isfinite(m), np.clip(m, 0.0, None), np.nan)
    node = np.nanmean(pos, axis=1)
    global_level = float(np.nanmean(pos)) if np.isfinite(pos).any() else np.nan
    return pd.Series(node, index=labels), global_level

def _rotate(series):
    s = series.sort_index()
    if len(s) > 1:
        s = pd.Series(np.roll(s.to_numpy(dtype=float), 1), index=s.index)
    return s.reindex(series.index)

def signals(data, window, mode="base"):
    close, liquid, residual = _context(data)
    ordered = sorted(close.columns)
    res = residual.reindex(columns=ordered)
    liq = liquid.reindex(columns=ordered)
    out = pd.DataFrame(0.0, index=close.index, columns=ordered)
    minp = max(16, window // 2)
    trend = res.rolling(TREND_DAYS, min_periods=max(5, TREND_DAYS // 2)).sum()
    for i, dt in enumerate(pd.DatetimeIndex(close.index)):
        if dt.dayofweek != 0 or i < window + GRAPH_LAG:
            continue
        active = [c for c in ordered if bool(liq.iloc[i][c]) and bool(liq.iloc[i-GRAPH_LAG][c])]
        if len(active) < 3:
            continue
        current = res.iloc[i-window+1:i+1][active]
        previous = res.iloc[i-GRAPH_LAG-window+1:i-GRAPH_LAG+1][active]
        cur_corr = current.corr(min_periods=minp).to_numpy(dtype=float)
        old_corr = previous.corr(min_periods=minp).to_numpy(dtype=float)
        if not (np.isfinite(cur_corr).all() and np.isfinite(old_corr).all()):
            continue
        cur_node, cur_global = _positive_stats(cur_corr, active)
        old_node, old_global = _positive_stats(old_corr, active)
        fragmentation = max(old_global - cur_global, 0.0)
        shedding = (old_node - cur_node).replace([np.inf, -np.inf], np.nan)
        if mode == "base":
            node = shedding
        elif mode == "ablation":
            node = (1.0 - cur_node).clip(lower=0.0)
        elif mode == "falsifier":
            node = _rotate(shedding)
        else:
            raise ValueError("unknown mode")
        trend_now = trend.loc[dt, active]
        raw = node.clip(lower=0.0) * fragmentation
        raw = raw.where(trend_now > 0, 0.0)
        out.loc[dt, active] = raw.fillna(0.0).to_numpy()
    return out.reindex(columns=close.columns), liquid

def _allocate(score, liquid, times, top_k):
    ranked = score.where(liquid & np.isfinite(score) & (score > 0)).sort_index(axis=1)
    selected = ranked.rank(axis=1, ascending=False, method="first") <= top_k
    target = selected.reindex(columns=score.columns).astype(float) * min(NAME_CAP, 1 / top_k)
    monday = pd.Series(pd.DatetimeIndex(times).dayofweek == 0, index=target.index)
    events = target.where(monday, axis=0).mask(~liquid, 0.0)
    weights = events.ffill(limit=6).fillna(0.0).where(liquid, 0.0)
    return xr.DataArray(weights.to_numpy(dtype=float), dims=("time", "asset"),
                        coords={"time": pd.DatetimeIndex(times), "asset": score.columns},
                        name=COMPETITION_TYPE)

def strategy(data, params=None, mode="base"):
    p = dict(PARAMS if params is None else params)
    if set(p) != {"window", "top_k"} or any(type(v) is not int or v < 1 for v in p.values()):
        raise ValueError("expected positive integer window and top_k")
    if p["window"] + GRAPH_LAG + TREND_DAYS + 40 >= LOOKBACK_DAYS:
        raise ValueError("parameters exceed bounded replay horizon")
    if mode not in {"base", "ablation", "falsifier"}:
        raise ValueError("unknown mode")
    times = pd.DatetimeIndex(data.time.values)
    if not times.is_unique or not times.is_monotonic_increasing or len(times) == 0:
        raise ValueError("nonempty increasing unique dates required")
    if len(set(data.asset.values.tolist())) != data.sizes["asset"]:
        raise ValueError("unique asset coordinates required")
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
