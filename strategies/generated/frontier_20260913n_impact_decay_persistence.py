"""Frontier-N residual impact decay persistence — IMPLEMENTED, UNMEASURED.

Experiment: frontier_20260913n_impact_decay_persistence
Preregistration SHA256: 05346beec4383c1cfd16264287c88b52e4dc5f04b905a6dccb8ea3775e236f87
Mechanism: falling residual absolute price displacement per unit eligible dollar-volume share.
No performance or submission claim.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
import xarray as xr
COMPETITION_TYPE="crypto_daily_long"; LOOKBACK_DAYS=365; NAME_CAP=0.25; TREND_DAYS=21; EPS=1e-12; IMPACT_LAG=21

def _field(data,name): return data.sel(field=name).transpose("time","asset").to_pandas().astype(float)
def _context(data):
    o=_field(data,"open").where(lambda x:np.isfinite(x)&(x>0)); h=_field(data,"high").where(lambda x:np.isfinite(x)&(x>0)); l=_field(data,"low").where(lambda x:np.isfinite(x)&(x>0)); c=_field(data,"close").where(lambda x:np.isfinite(x)&(x>0)); v=_field(data,"vol").where(lambda x:np.isfinite(x)&(x>0)); liquid=_field(data,"is_liquid").eq(1)&c.notna(); r=np.log(c/c.shift(1)); market=r.where(liquid).sort_index(axis=1).mean(axis=1); return o,h,l,c,v,liquid,r.sub(market,axis=0)
def _pct_rank(values,eligible):
    ordered=values.sort_index(axis=1); mask=eligible.reindex(columns=ordered.columns).fillna(False); return ordered.where(mask).rank(axis=1,pct=True,method="first").reindex(columns=values.columns)
def _rotate_eligible(values,eligible):
    ordered=values.sort_index(axis=1); mask=eligible.reindex(columns=ordered.columns).fillna(False); out=ordered.copy()
    for i in range(len(out)):
        arr=out.iloc[i].to_numpy(dtype=float).copy(); loc=np.flatnonzero(mask.iloc[i].to_numpy(dtype=bool)&np.isfinite(arr))
        if len(loc)>1: arr[loc]=np.roll(arr[loc],1); out.iloc[i]=arr
    return out.reindex(columns=values.columns)
def _allocate(score,liquid,times,top_k):
    ranked=score.where(liquid&np.isfinite(score)&(score>0)).sort_index(axis=1); selected=ranked.rank(axis=1,ascending=False,method="first")<=top_k; selected=selected.reindex(columns=score.columns); target=selected.astype(float)*min(NAME_CAP,1.0/top_k); monday=pd.Series(pd.DatetimeIndex(times).dayofweek==0,index=target.index); events=target.where(monday,axis=0).mask(~liquid,0.0); weights=events.ffill(limit=6).fillna(0.0).where(liquid,0.0); return xr.DataArray(weights.to_numpy(dtype=float),dims=("time","asset"),coords={"time":times,"asset":score.columns},name=COMPETITION_TYPE)
def load_data(period):
    os.environ.setdefault("API_KEY","default"); import qnt.data as qndata; return qndata.cryptodaily_load_data(tail=period)
def signals(data,window,mode="base"):
    _,_,_,c,v,liquid,residual=_context(data); dollar=(c*v).where(liquid); total=dollar.sort_index(axis=1).sum(axis=1,min_count=1).replace(0,np.nan); share=dollar.div(total,axis=0); impact=np.log1p(residual.abs()/(share+1e-8)); minp=max(7,window//2); level=impact.rolling(window,min_periods=minp).mean(); decay=level.shift(IMPACT_LAG)-level; low_impact=1.0-_pct_rank(level,liquid)
    if mode=="base": node=decay
    elif mode=="ablation": node=low_impact
    elif mode=="falsifier": node=_rotate_eligible(decay,liquid)
    else: raise ValueError("unknown mode")
    trend=residual.rolling(TREND_DAYS,min_periods=10).sum(); score=node.clip(lower=0.0)*trend.clip(lower=0.0); return score.replace([np.inf,-np.inf],np.nan),liquid
PARAMS={"window":42,"top_k":5}; FAMILY="impact_decay_persistence"
def strategy(data,params=None,mode="base"):
    p=dict(PARAMS if params is None else params)
    if set(p)!={"window","top_k"} or any(type(v) is not int or v<1 for v in p.values()): raise ValueError("expected positive integer window and top_k")
    if p["window"] not in {21,42,63} or p["top_k"]!=5: raise ValueError("outside preregistered Frontier-N grid")
    if p["window"]+70>=LOOKBACK_DAYS: raise ValueError("parameters exceed finite replay horizon")
    if mode not in {"base","ablation","falsifier"}: raise ValueError("unknown mode")
    score,liquid=signals(data,p["window"],mode); return _allocate(score,liquid,data.time,p["top_k"])
if __name__=="__main__":
    os.environ.setdefault("API_KEY","default"); import qnt.backtester as qnbt; qnbt.backtest(competition_type=COMPETITION_TYPE,load_data=load_data,lookback_period=LOOKBACK_DAYS,start_date="2016-01-01",strategy=strategy,analyze=True,check_correlation=True)
