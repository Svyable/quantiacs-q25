"""Ebenezar-profile Q25 translation: dual_sharpe_classifier — IMPLEMENTED, UNMEASURED.

Experiment: ebenezar_20260912_dual_sharpe_classifier
Preregistration SHA256: 63d6e18b215401c8ac9adb730879a6ef9490aad7cb57b6605798eeabfadd8a0b

This is explicitly a user-directed family-refinement screen, not a novelty claim.
It uses only completed Quantiacs daily OHLCV plus historical is_liquid, is long
only, automatic, capped at 25% per name, and permits cash.
"""
from __future__ import annotations
import os
import numpy as np
import xarray as xr
COMPETITION_TYPE="crypto_daily_long"; LOOKBACK_DAYS=365; NAME_CAP=0.25; EPS=1e-12

def _close_liquid(data):
    close=data.sel(field="close").transpose("time","asset").astype(float); liq0=data.sel(field="is_liquid").transpose("time","asset")
    return close, xr.where((liq0==1)&np.isfinite(close)&(close>0),1.0,0.0)
def _returns(close):
    r=close/close.shift(time=1)-1.0; return xr.where(np.isfinite(r),r,0.0)
def _sma(x,n,min_periods=None):
    m=n if min_periods is None else min_periods
    if x.sizes["time"]<m: return xr.full_like(x,np.nan,dtype=float)
    with xr.set_options(use_bottleneck=False):
        return x.rolling(time=min(n,x.sizes["time"]),min_periods=m).mean()
def _std(x,n,min_periods=None):
    m=max(2,n//2) if min_periods is None else min_periods
    if x.sizes["time"]<m: return xr.full_like(x,np.nan,dtype=float)
    with xr.set_options(use_bottleneck=False):
        return x.rolling(time=min(n,x.sizes["time"]),min_periods=m).std()
def _liquid_cs_mean(x,liquid):
    n=liquid.sum("asset"); return xr.where(n>0,(xr.where(np.isfinite(x),x,0.0)*liquid).sum("asset")/n,0.0)
def _allocate(raw,liquid):
    raw=xr.where(np.isfinite(raw)&(raw>0),raw,0.0)*liquid; gross=raw.sum("asset"); normalized=xr.where(gross>EPS,raw/gross,0.0); capped=xr.where(normalized>NAME_CAP,NAME_CAP,normalized)*liquid
    return capped.transpose("time","asset").fillna(0.0).reset_coords("field",drop=True)
def _params(params,window):
    p={"window":window} if params is None else dict(params)
    if set(p)!={"window"} or p["window"]!=window: raise ValueError(f"expected frozen window={window}")
def load_data(period):
    os.environ.setdefault("API_KEY","default"); import qnt.data as qndata; return qndata.cryptodaily_load_data(tail=period)
def _run_backtest(fn):
    os.environ.setdefault("API_KEY","default"); import qnt.backtester as qnbt; qnbt.backtest(competition_type=COMPETITION_TYPE,load_data=load_data,lookback_period=LOOKBACK_DAYS,start_date="2016-01-01",strategy=fn,analyze=True,check_correlation=True)

def strategy(data,params=None,mode="base"):
    _params(params,7)
    if mode!="base": raise ValueError("this translation screen freezes base mode only")
    close,liquid=_close_liquid(data); r=_returns(close); vol14=_std(r,14,7); vol28=_std(r,28,14)
    s3=np.sqrt(365.0)*_sma(r,3,3)/(vol14+EPS); s7=np.sqrt(365.0)*_sma(r,7,5)/(vol28+EPS); s21=np.sqrt(365.0)*_sma(r,21,12)/(vol28+EPS)
    sma21=_sma(close,21,12); sma55=_sma(close,55,28); mom14=close/close.shift(time=14)-1.0; s3_h=_liquid_cs_mean(s3,liquid); vol_h=_liquid_cs_mean(vol14,liquid)*1.15
    votes=(xr.where(s3>s3_h,1.0,0.0)+xr.where(s7>0.0,1.0,0.0)+xr.where(s3>s21,1.0,0.0)+xr.where((close>sma21)&(sma21>sma55),1.0,0.0)+xr.where(mom14>0.0,1.0,0.0)+xr.where(vol14<vol_h,1.0,0.0))
    quality=(xr.where(s3>0.0,s3,0.0)+0.70*xr.where(s7>0.0,s7,0.0)+0.30*xr.where(s3>s21,s3-s21,0.0)).clip(min=0.0,max=25.0)
    raw=xr.where(votes>=4.0,quality/(vol28+0.015),0.0)*liquid; raw=_sma(raw,3,1)*liquid
    return _allocate(raw,liquid)
if __name__=="__main__": _run_backtest(strategy)
