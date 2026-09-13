"""Ebenezar-profile Q25 translation: lattice_consensus — IMPLEMENTED, UNMEASURED.

Experiment: ebenezar_20260912_lattice_consensus
Preregistration SHA256: e838918ae7c19e118ca51cfaa3c49f1aad686c48eba04731344367ea6b217860

User-directed family-refinement screen; not a novelty claim. The name refers only to progressive candidate filtering, not to a learned LDT. Quantiacs OHLCV + historical is_liquid only; long-only, automatic, 25% name cap, cash allowed.
"""
from __future__ import annotations
import os
import numpy as np
import xarray as xr
COMPETITION_TYPE="crypto_daily_long"; LOOKBACK_DAYS=365; NAME_CAP=0.25; EPS=1e-12

def _base(data):
    c=data.sel(field="close").transpose("time","asset").astype(float); z=data.sel(field="is_liquid").transpose("time","asset"); l=xr.where((z==1)&np.isfinite(c)&(c>0),1.0,0.0); r=c/c.shift(time=1)-1.0; return c,l,xr.where(np.isfinite(r),r,0.0)
def _sma(x,n,m):
    if x.sizes["time"]<m: return xr.full_like(x,np.nan,dtype=float)
    return x.rolling(time=min(n,x.sizes["time"]),min_periods=m).mean()
def _std(x,n,m):
    if x.sizes["time"]<m: return xr.full_like(x,np.nan,dtype=float)
    return x.rolling(time=min(n,x.sizes["time"]),min_periods=m).std()
def _max(x,n,m):
    if x.sizes["time"]<m: return xr.full_like(x,np.nan,dtype=float)
    return x.rolling(time=min(n,x.sizes["time"]),min_periods=m).max()
def _mean(x,l):
    n=l.sum("asset"); return xr.where(n>0,(xr.where(np.isfinite(x),x,0.0)*l).sum("asset")/n,0.0)
def _alloc(raw,l):
    raw=xr.where(np.isfinite(raw)&(raw>0),raw,0.0)*l; g=raw.sum("asset"); w=xr.where(g>EPS,raw/g,0.0); return ((xr.where(w>NAME_CAP,NAME_CAP,w)*l).transpose("time","asset").fillna(0.0).reset_coords("field",drop=True))
def load_data(period):
    os.environ.setdefault("API_KEY","default"); import qnt.data as qndata; return qndata.cryptodaily_load_data(tail=period)
def strategy(data,params=None,mode="base"):
    p={"window":7} if params is None else dict(params)
    if p!={"window":7} or mode!="base": raise ValueError("frozen base window=7 only")
    c,l,r=_base(data); v=_std(r,21,10); s=np.sqrt(365.0)*_sma(r,7,5)/(v+EPS); sma18=_sma(c,18,10); sma50=_sma(c,50,25); trend=sma18/(sma50+EPS)-1.0; mom=c/c.shift(time=14)-1.0; peak=_max(c,42,20); dd=c/(peak+EPS)-1.0; ms=_mean(s,l); mv=_mean(v,l)
    support=(xr.where(trend>0,1.0,0.0)+xr.where(s>ms,1.0,0.0)+xr.where(mom>0,1.0,0.0)+xr.where(v<1.25*mv,1.0,0.0)+xr.where(dd>-0.25,1.0,0.0))
    quality=(xr.where(s>ms,s-ms,0.0)+2*xr.where(trend>0,trend,0.0)+xr.where(mom>0,mom,0.0))*(support/5.0); raw=xr.where(support>=4.0,quality/(v+0.015),0.0)*l; raw=_sma(raw,5,1)*l
    return _alloc(raw,l)
if __name__=="__main__":
    os.environ.setdefault("API_KEY","default"); import qnt.backtester as qnbt; qnbt.backtest(competition_type=COMPETITION_TYPE,load_data=load_data,lookback_period=LOOKBACK_DAYS,start_date="2016-01-01",strategy=strategy,analyze=True,check_correlation=True)
