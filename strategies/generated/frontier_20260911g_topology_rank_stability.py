"""frontier_20260911g_topology_rank_stability — PENDING RESEARCH STRATEGY.
Experiment: frontier_20260911g_topology_rank_stability
Preregistration SHA256: 6152bf212ba044cafe3c3c7b539247ee2013707351b7228d81aff0903a0eb4b8
Mechanism: stable residual-topology rank during raw leadership churn.
Nearest incumbent: topology migration / V10 residual momentum.
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

FAMILY = "topology_rank_stability"

def signals(data, window, mode="base"):
    c, liquid, r, market, residual = _base_panel(data)
    ordered = sorted(c.columns)
    res = residual.reindex(columns=ordered)
    raw_r = r.reindex(columns=ordered)
    out = pd.DataFrame(0.0,index=c.index,columns=ordered)
    times = pd.DatetimeIndex(c.index)
    minp=max(16,window//2)
    first=window+STATE_LAG+TREND_DAYS+2
    for i in range(first,len(times)):
        if times[i].dayofweek != 0: continue
        cur = res.iloc[i-window+1:i+1]
        prev_end=i-STATE_LAG
        prev = res.iloc[prev_end-window+1:prev_end+1]
        cur_cent,_ = _centrality(cur,minp)
        prev_cent,_ = _centrality(prev,minp)
        if cur_cent.empty or prev_cent.empty: continue
        cur_rank=cur_cent.rank(method="average",pct=True)
        prev_rank=prev_cent.rank(method="average",pct=True)
        if mode=="falsifier":
            cur_rank=pd.Series(np.roll(cur_rank.to_numpy(float),1),index=cur_rank.index)
            prev_rank=pd.Series(np.roll(prev_rank.to_numpy(float),1),index=prev_rank.index)
        periphery=(1.0-cur_rank).clip(lower=0.0)
        stability=(1.0-(cur_rank-prev_rank).abs()).clip(lower=0.0)
        now=raw_r.iloc[i-TREND_DAYS+1:i+1].sum(min_count=max(5,TREND_DAYS//2))
        old=raw_r.iloc[prev_end-TREND_DAYS+1:prev_end+1].sum(min_count=max(5,TREND_DAYS//2))
        churn=(now.rank(method="average",pct=True)-old.rank(method="average",pct=True)).abs()
        residual_trend=res.iloc[i-TREND_DAYS+1:i+1].sum(min_count=max(5,TREND_DAYS//2))
        if mode=="ablation":
            node=periphery
        elif mode in {"base","falsifier"}:
            node=periphery*stability*churn
        else: raise ValueError("unknown control mode")
        out.iloc[i]=(node.where(residual_trend>0,0.0)).reindex(ordered).fillna(0.0).to_numpy()
    return out.reindex(columns=c.columns), liquid

def strategy(data, params=None, mode="base"):
    p=dict(PARAMS if params is None else params); _validate(data,p,mode)
    score,liquid=signals(data,p["window"],mode)
    return _allocate(score,liquid,data.time,p["top_k"])

def load_data(period):
    import qnt.data as qndata
    return qndata.cryptodaily_load_data(tail=period)
