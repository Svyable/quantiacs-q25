"""frontier_20260911g_response_sign_asymmetry — PENDING RESEARCH STRATEGY.
Experiment: frontier_20260911g_response_sign_asymmetry
Preregistration SHA256: 7f8ec7b0693d65af6797529bcae730d996a561e861e36a0f1f6f26b3c6a44fe1
Mechanism: positive-vs-negative common-shock assimilation asymmetry.
Nearest incumbent: symmetric assimilation delay / seesaw.
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

FAMILY = "response_sign_asymmetry"
MAX_LAG=3

def _lag_centroid(y, market, window, i, sign=None):
    idx=slice(i-window+1,i+1)
    weights=[]
    for lag in range(MAX_LAG+1):
        x=market.shift(lag).iloc[idx]
        yy=y.iloc[idx]
        if sign=="positive":
            mask=x>0
        elif sign=="negative":
            mask=x<0
        else:
            mask=x.notna()
        xx=x.where(mask)
        xv=xx.to_numpy(dtype=float)
        betas=[]
        for col in yy.columns:
            yv=yy[col].to_numpy(dtype=float)
            m=np.isfinite(xv)&np.isfinite(yv)
            if m.sum()<max(10,window//5):
                betas.append(np.nan); continue
            xs=xv[m]; ys=yv[m]
            var=np.var(xs)
            betas.append(np.cov(xs,ys,ddof=0)[0,1]/var if var>1e-10 else np.nan)
        weights.append(np.abs(np.asarray(betas,float)))
    w=np.vstack(weights)
    num=np.nansum(w*np.arange(MAX_LAG+1)[:,None],axis=0)
    den=np.nansum(w,axis=0)
    vals=np.where(den>1e-10,num/den,np.nan)
    return pd.Series(vals,index=y.columns)

def signals(data, window, mode="base"):
    c, liquid, r, market, residual=_base_panel(data)
    ordered=sorted(c.columns)
    rr=r.reindex(columns=ordered); res=residual.reindex(columns=ordered)
    out=pd.DataFrame(0.0,index=c.index,columns=ordered)
    times=pd.DatetimeIndex(c.index)
    first=window+STATE_LAG+TREND_DAYS+MAX_LAG+2
    for i in range(first,len(times)):
        if times[i].dayofweek != 0: continue
        pos=_lag_centroid(rr,market,window,i,"positive")
        neg=_lag_centroid(rr,market,window,i,"negative")
        pooled=_lag_centroid(rr,market,window,i,None)
        trend=res.iloc[i-TREND_DAYS+1:i+1].sum(min_count=max(5,TREND_DAYS//2))
        if mode=="base":
            node=(neg-pos).clip(lower=0.0)
        elif mode=="falsifier":
            node=(pos-neg).clip(lower=0.0)
        elif mode=="ablation":
            node=(MAX_LAG-pooled).clip(lower=0.0)
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
