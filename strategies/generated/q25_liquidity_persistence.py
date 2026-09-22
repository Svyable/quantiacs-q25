"""Preregistered liquidity-persistence candidate using only historical contest eligibility and close."""
import numpy as np
import xarray as xr
COMPETITION_TYPE="crypto_daily_long"; STRATEGY_ID="q25_liquidity_persistence_v1"; LOOKBACK_DAYS=180; NAME_CAP=0.25; EPS=1e-12

def calculate_weights(data):
    c=data.sel(field="close").transpose("time","asset").astype(float)
    l=xr.where((data.sel(field="is_liquid").transpose("time","asset")==1)&np.isfinite(c)&(c>0),1.0,0.0)
    persistence=l.rolling(time=30,min_periods=20).mean()
    mom=c/c.shift(time=28)-1; r=c/c.shift(time=1)-1; vol=r.rolling(time=21,min_periods=14).std()
    # Favor assets repeatedly eligible in the sponsor-provided liquid universe, not one-day entrants.
    raw=(mom.clip(min=0.0)**1.1)*(persistence**2)/(vol+0.015)*l
    raw=raw.rolling(time=4,min_periods=1).mean()*l
    gross=raw.sum("asset"); w=xr.where(gross>EPS,raw/gross,0.0)
    return xr.where(w>NAME_CAP,NAME_CAP,w).fillna(0.0).transpose("time","asset")
def strategy(data): return calculate_weights(data)
def load_data(period):
    import qnt.data as qndata
    return qndata.cryptodaily_load_data(tail=max(int(period),LOOKBACK_DAYS))
