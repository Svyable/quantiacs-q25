"""frontier_20260911g_topology_reconnection — PENDING RESEARCH STRATEGY.
Experiment: frontier_20260911g_topology_reconnection
Preregistration SHA256: 874e50365070e746d80744a62b88373518b141787c93acceeed9e4116278176c
Mechanism: reconnection from residual-network periphery after fragmentation.
Nearest incumbent: topology migration.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
PARAMS = {"window": 63, "top_k": 5}
STATE_LAG = 21
TREND_DAYS = 21

def _field(data, name):
    return data.sel(field=name).transpose("time","asset").to_pandas().astype(float)

def _base_panel(data):
    c = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = _field(data, "is_liquid").eq(1) & c.notna()
    r = np.log(c / c.shift(1))
    market = r.where(liquid).mean(axis=1)
    residual = r.sub(market, axis=0)
    return c, liquid, r, market, residual

def _centrality(frame, min_periods):
    corr = frame.corr(min_periods=min_periods)
    vals = corr.to_numpy(dtype=float).copy()
    if vals.size == 0:
        return pd.Series(dtype=float), np.nan
    np.fill_diagonal(vals, np.nan)
    cent = np.nanmean(np.abs(vals), axis=1)
    glob = float(np.nanmean(np.abs(vals))) if np.isfinite(vals).any() else np.nan
    return pd.Series(cent,index=corr.index), glob

def _allocate(score, liquid, times, top_k):
    ranked = score.where(liquid & (score > 0)).sort_index(axis=1)
    selected = ranked.rank(axis=1, ascending=False, method="first") <= top_k
    selected = selected.reindex(columns=score.columns)
    raw = selected.astype(float) * min(NAME_CAP, 1/top_k)
    monday = pd.Series(pd.DatetimeIndex(times).dayofweek == 0, index=raw.index)
    weights = raw.where(monday,axis=0).ffill(limit=6).fillna(0.0)
    weights = weights.where(liquid,0.0)
    return xr.DataArray(weights.to_numpy(dtype=float),dims=("time","asset"),
                        coords={"time":times,"asset":score.columns},name=COMPETITION_TYPE)

def _validate(data,p,mode):
    if set(p) != {"window","top_k"}:
        raise ValueError("expected exactly window, top_k")
    if any(type(v) is not int or v < 1 for v in p.values()):
        raise ValueError("parameters must be positive integers")
    if 2*p["window"] + 2*STATE_LAG + TREND_DAYS + 14 >= LOOKBACK_DAYS:
        raise ValueError("parameters exceed finite replay horizon")
    if mode not in {"base","ablation","falsifier"}:
        raise ValueError("unknown control mode")
    times = pd.DatetimeIndex(data.time.values)
    if not times.is_unique or not times.is_monotonic_increasing:
        raise ValueError("times must be unique and increasing")
    if len(set(data.asset.values.tolist())) != data.sizes["asset"]:
        raise ValueError("assets must be unique")

FAMILY = "topology_reconnection"

def signals(data, window, mode="base"):
    c, liquid, r, market, residual = _base_panel(data)
    ordered=sorted(c.columns); res=residual.reindex(columns=ordered)
    out=pd.DataFrame(0.0,index=c.index,columns=ordered)
    times=pd.DatetimeIndex(c.index); minp=max(16,window//2)
    first=window+STATE_LAG+TREND_DAYS+2
    for i in range(first,len(times)):
        if times[i].dayofweek != 0: continue
        cur=res.iloc[i-window+1:i+1]
        prev_end=i-STATE_LAG
        prev=res.iloc[prev_end-window+1:prev_end+1]
        cur_cent,cur_global=_centrality(cur,minp)
        prev_cent,prev_global=_centrality(prev,minp)
        if not np.isfinite(cur_global) or not np.isfinite(prev_global): continue
        reconnection=(cur_cent-prev_cent).clip(lower=0.0)
        prior_periphery=(prev_cent.median()-prev_cent).clip(lower=0.0)
        global_reconnect=max(cur_global-prev_global,0.0)
        trend=res.iloc[i-TREND_DAYS+1:i+1].sum(min_count=max(5,TREND_DAYS//2))
        if mode=="ablation":
            node=cur_cent.clip(lower=0.0)
        elif mode=="falsifier":
            vals=reconnection.to_numpy(float)
            node=pd.Series(np.roll(vals,1),index=reconnection.index)*prior_periphery*global_reconnect
        elif mode=="base":
            node=reconnection*prior_periphery*global_reconnect
        else: raise ValueError("unknown control mode")
        out.iloc[i]=node.where(trend>0,0.0).reindex(ordered).fillna(0.0).to_numpy()
    return out.reindex(columns=c.columns), liquid

def strategy(data, params=None, mode="base"):
    p=dict(PARAMS if params is None else params); _validate(data,p,mode)
    score,liquid=signals(data,p["window"],mode)
    return _allocate(score,liquid,data.time,p["top_k"])

def load_data(period):
    import qnt.data as qndata
    return qndata.cryptodaily_load_data(tail=period)
