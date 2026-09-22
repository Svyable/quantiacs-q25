"""Volatility-contraction breakout: favor positive breakouts emerging from unusually quiet recent volatility."""
import numpy as np
import xarray as xr
COMPETITION_TYPE="crypto_daily_long"; STRATEGY_ID="q25_volatility_contraction_breakout_v1"; LOOKBACK_DAYS=180; NAME_CAP=.25; EPS=1e-12
def calculate_weights(data):
 c=data.sel(field="close").transpose("time","asset").astype(float); l=xr.where((data.sel(field="is_liquid").transpose("time","asset")==1)&np.isfinite(c)&(c>0),1.,0.)
 r=c/c.shift(time=1)-1; v14=r.rolling(time=14,min_periods=10).std(); v56=r.rolling(time=56,min_periods=35).std()
 peak=c.shift(time=1).rolling(time=28,min_periods=20).max(); breakout=(c/(peak+EPS)-1).clip(min=0)
 contraction=(1-v14/(v56+EPS)).clip(min=0,max=1); raw=breakout*contraction/(v14+.01)*l
 raw=raw.rolling(time=3,min_periods=1).mean()*l; g=raw.sum("asset"); w=xr.where(g>EPS,raw/g,0.)
 return xr.where(w>NAME_CAP,NAME_CAP,w).fillna(0).transpose("time","asset")
def strategy(data): return calculate_weights(data)
def load_data(period):
 import qnt.data as qndata
 return qndata.cryptodaily_load_data(tail=max(int(period),LOOKBACK_DAYS))
