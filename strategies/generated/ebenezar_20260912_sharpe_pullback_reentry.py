"""Ebenezar-profile Q25 translation: sharpe_pullback_reentry — IMPLEMENTED, UNMEASURED.

Experiment: ebenezar_20260912_sharpe_pullback_reentry
Preregistration SHA256: 643de7d1bf8607de00d790d56d7c73e551dedd859984ecf10135e1996b38e2b6

User-directed family-refinement screen; not a novelty claim. Quantiacs daily OHLCV + historical is_liquid only; long-only, automatic, 25% name cap, cash allowed.
"""
from __future__ import annotations
import os
import numpy as np
import xarray as xr
COMPETITION_TYPE="crypto_daily_long"; LOOKBACK_DAYS=365; NAME_CAP=0.25; EPS=1e-12

def _base(data):
    c=data.sel(field="close").transpose("time","asset").astype(float); z=data.sel(field="is_liquid").transpose("time","asset"); l=xr.where((z==1)&np.isfinite(c)&(c>0),1.0,0.0); r=c/c.shift(time=1)-1.0; return c,l,xr.where(np.isfinite(r),r,0.0)
def _sma(x,n,m): return x.rolling(time=n,min_periods=m).mean()
def _std(x,n,m): return x.rolling(time=n,min_periods=m).std()
def _mean(x,l):
    n=l.sum("asset"); return xr.where(n>0,(xr.where(np.isfinite(x),x,0.0)*l).sum("asset")/n,0.0)
def _alloc(raw,l):
    raw=xr.where(np.isfinite(raw)&(raw>0),raw,0.0)*l; g=raw.sum("asset"); w=xr.where(g>EPS,raw/g,0.0); return ((xr.where(w>NAME_CAP,NAME_CAP,w)*l).transpose("time","asset").fillna(0.0).reset_coords("field",drop=True))
def load_data(period):
    os.environ.setdefault("API_KEY","default"); import qnt.data as qndata; return qndata.cryptodaily_load_data(tail=period)
def strategy(data,params=None,mode="base"):
    p={"window":21} if params is None else dict(params)
    if p!={"window":21} or mode!="base": raise ValueError("frozen base window=21 only")
    c,l,r=_base(data); v=_std(r,28,14); s=np.sqrt(365.0)*_sma(r,21,12)/(v+EPS); mom3=c/c.shift(time=3)-1.0; mom21=c/c.shift(time=21)-1.0; sma55=_sma(c,55,28); up=xr.where(r>0,r,0.0); down=xr.where(r<0,-r,0.0); rs=_sma(up,14,8)/(_sma(down,14,8)+EPS); rsi=100.0-100.0/(1.0+rs); ms=_mean(s,l)
    gate=(s>ms)&(s>0)&(mom21>0)&(c>sma55)&(mom3<0)&(mom3>-0.18)&(rsi<55.0)&(v>0); pull=(-mom3).clip(min=0.0,max=0.18); quality=(s-ms).clip(min=0.0)*(0.02+pull); raw=xr.where(gate,quality/(v+0.015),0.0)*l; raw=_sma(raw,3,1)*l
    return _alloc(raw,l)
if __name__=="__main__":
    os.environ.setdefault("API_KEY","default"); import qnt.backtester as qnbt; qnbt.backtest(competition_type=COMPETITION_TYPE,load_data=load_data,lookback_period=LOOKBACK_DAYS,start_date="2016-01-01",strategy=strategy,analyze=True,check_correlation=True)
