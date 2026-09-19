"""Ebenezar-profile Q25 translation: residual_sharpe — IMPLEMENTED, UNMEASURED.

Experiment: ebenezar_20260912_residual_sharpe
Preregistration SHA256: c0cdffae445bd8e2f564da27df262b5f1e9939b10fc2a5d4681bfe3699aff82b

User-directed family-refinement screen; not a novelty claim. Uses only completed Quantiacs daily OHLCV and historical is_liquid; long-only, automatic, 25% name cap, cash allowed.
"""
from __future__ import annotations
import os
import numpy as np
import xarray as xr
COMPETITION_TYPE="crypto_daily_long"; LOOKBACK_DAYS=365; NAME_CAP=0.25; EPS=1e-12

def _base(data):
    c=data.sel(field="close").transpose("time","asset").astype(float); z=data.sel(field="is_liquid").transpose("time","asset"); l=xr.where((z==1)&np.isfinite(c)&(c>0),1.0,0.0); r=c/c.shift(time=1)-1.0; r=xr.where(np.isfinite(r),r,0.0); return c,l,r
def _sma(x,n,m):
    if x.sizes["time"]<m: return xr.full_like(x,np.nan,dtype=float)
    with xr.set_options(use_bottleneck=False):
        return x.rolling(time=min(n,x.sizes["time"]),min_periods=m).mean()
def _std(x,n,m):
    if x.sizes["time"]<m: return xr.full_like(x,np.nan,dtype=float)
    with xr.set_options(use_bottleneck=False):
        return x.rolling(time=min(n,x.sizes["time"]),min_periods=m).std()
def _mean(x,l):
    n=l.sum("asset"); return xr.where(n>0,(xr.where(np.isfinite(x),x,0.0)*l).sum("asset")/n,0.0)
def _sd(x,l):
    mu=_mean(x,l); n=l.sum("asset"); v=xr.where(n>0,(((xr.where(np.isfinite(x),x,0.0)-mu)**2)*l).sum("asset")/n,0.0); return np.sqrt(xr.where(v>0,v,0.0))
def _alloc(raw,l):
    raw=xr.where(np.isfinite(raw)&(raw>0),raw,0.0)*l; g=raw.sum("asset"); w=xr.where(g>EPS,raw/g,0.0); return ((xr.where(w>NAME_CAP,NAME_CAP,w)*l).transpose("time","asset").fillna(0.0).reset_coords("field",drop=True))
def load_data(period):
    os.environ.setdefault("API_KEY","default"); import qnt.data as qndata; return qndata.cryptodaily_load_data(tail=period)
def strategy(data,params=None,mode="base"):
    p={"window":7} if params is None else dict(params)
    if p!={"window":7} or mode!="base": raise ValueError("frozen base window=7 only")
    c,l,r=_base(data); residual=r-_mean(r,l); rv=_std(residual,21,10); s=np.sqrt(365.0)*_sma(residual,7,5)/(rv+EPS); h=_mean(s,l)+0.15*_sd(s,l)
    mom=c/c.shift(time=21)-1.0; trend=c/(_sma(c,30,18)+EPS)-1.0; raw=xr.where((s>h)&(mom>0)&(trend>0)&(rv>0),(s-h).clip(min=0.0)/(rv+0.01),0.0)*l; raw=_sma(raw,3,1)*l
    return _alloc(raw,l)
if __name__=="__main__":
    os.environ.setdefault("API_KEY","default"); import qnt.backtester as qnbt; qnbt.backtest(competition_type=COMPETITION_TYPE,load_data=load_data,lookback_period=LOOKBACK_DAYS,start_date="2016-01-01",strategy=strategy,analyze=True,check_correlation=True)
