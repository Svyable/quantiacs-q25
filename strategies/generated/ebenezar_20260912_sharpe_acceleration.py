"""Ebenezar-profile Q25 translation: sharpe_acceleration — IMPLEMENTED, UNMEASURED.

Experiment: ebenezar_20260912_sharpe_acceleration
Preregistration SHA256: 35078edff67b24625a71e559d23cc8f12e9685a401a1c6675992762b09bd7c0a

User-directed family-refinement screen; not a novelty claim. Quantiacs daily OHLCV plus historical is_liquid only; long-only, automatic, capped at 25% per name, cash permitted.
"""
from __future__ import annotations
import os
import numpy as np
import xarray as xr
COMPETITION_TYPE="crypto_daily_long"; LOOKBACK_DAYS=365; NAME_CAP=0.25; EPS=1e-12

def _close_liquid(data):
    c=data.sel(field="close").transpose("time","asset").astype(float); l=data.sel(field="is_liquid").transpose("time","asset"); return c,xr.where((l==1)&np.isfinite(c)&(c>0),1.0,0.0)
def _returns(c):
    r=c/c.shift(time=1)-1.0; return xr.where(np.isfinite(r),r,0.0)
def _sma(x,n,m=None): return x.rolling(time=n,min_periods=n if m is None else m).mean()
def _std(x,n,m=None): return x.rolling(time=n,min_periods=max(2,n//2) if m is None else m).std()
def _mean(x,l):
    n=l.sum("asset"); return xr.where(n>0,(xr.where(np.isfinite(x),x,0.0)*l).sum("asset")/n,0.0)
def _sd(x,l):
    mu=_mean(x,l); n=l.sum("asset"); v=xr.where(n>0,(((xr.where(np.isfinite(x),x,0.0)-mu)**2)*l).sum("asset")/n,0.0); return np.sqrt(xr.where(v>0,v,0.0))
def _alloc(raw,l):
    raw=xr.where(np.isfinite(raw)&(raw>0),raw,0.0)*l; g=raw.sum("asset"); w=xr.where(g>EPS,raw/g,0.0); return xr.where(w>NAME_CAP,NAME_CAP,w).mul(l).transpose("time","asset").fillna(0.0)
def load_data(period):
    os.environ.setdefault("API_KEY","default"); import qnt.data as qndata; return qndata.cryptodaily_load_data(tail=period)
def strategy(data,params=None,mode="base"):
    p={"window":3} if params is None else dict(params)
    if p!={"window":3} or mode!="base": raise ValueError("frozen base window=3 only")
    c,l=_close_liquid(data); r=_returns(c); v=_std(r,21,10); s3=np.sqrt(365.0)*_sma(r,3,3)/(v+EPS); s14=np.sqrt(365.0)*_sma(r,14,8)/(v+EPS); a=s3-s14
    trend=c/(_sma(c,20,12)+EPS)-1.0; mom=c/c.shift(time=7)-1.0; h=_mean(a,l)+0.25*_sd(a,l)
    raw=xr.where((a>h)&(s3>0)&(mom>0)&(trend>0)&(v>0),(a-h).clip(min=0.0)/(v+0.01),0.0)*l; raw=_sma(raw,4,1)*l
    return _alloc(raw,l)
if __name__=="__main__":
    os.environ.setdefault("API_KEY","default"); import qnt.backtester as qnbt; qnbt.backtest(competition_type=COMPETITION_TYPE,load_data=load_data,lookback_period=LOOKBACK_DAYS,start_date="2016-01-01",strategy=strategy,analyze=True,check_correlation=True)
