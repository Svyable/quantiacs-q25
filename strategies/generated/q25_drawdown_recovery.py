"""Drawdown-recovery alpha: positive medium trend plus recovery from a recent non-catastrophic drawdown."""
import numpy as np
import xarray as xr
COMPETITION_TYPE="crypto_daily_long"; STRATEGY_ID="q25_drawdown_recovery_v1"; LOOKBACK_DAYS=180; NAME_CAP=.25; EPS=1e-12
def calculate_weights(data):
 c=data.sel(field="close").transpose("time","asset").astype(float); l=xr.where((data.sel(field="is_liquid").transpose("time","asset")==1)&np.isfinite(c)&(c>0),1.,0.)
 r=c/c.shift(time=1)-1; vol=r.rolling(time=28,min_periods=14).std(); peak=c.rolling(time=42,min_periods=28).max(); dd=c/(peak+EPS)-1
 recovery=(c/c.shift(time=7)-1).clip(min=0); trend=(c/c.shift(time=42)-1).clip(min=0)
 sweet=xr.where((dd<-.03)&(dd>-.22),1.,0.); raw=recovery*trend* sweet/(vol+.012)*l
 raw=raw.rolling(time=3,min_periods=1).mean()*l; g=raw.sum("asset"); w=xr.where(g>EPS,raw/g,0.)
 return xr.where(w>NAME_CAP,NAME_CAP,w).fillna(0).clip(min=0).transpose("time","asset")
def strategy(data): return calculate_weights(data)
def load_data(period):
 import qnt.data as qndata
 return qndata.cryptodaily_load_data(tail=max(int(period),LOOKBACK_DAYS))
