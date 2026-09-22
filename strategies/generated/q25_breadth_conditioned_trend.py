"""Preregistered breadth-conditioned trend candidate; exposure emerges from cross-sectional breadth."""
import numpy as np
import xarray as xr
COMPETITION_TYPE="crypto_daily_long"; STRATEGY_ID="q25_breadth_conditioned_trend_v1"; LOOKBACK_DAYS=180; NAME_CAP=0.25; EPS=1e-12

def calculate_weights(data):
    c=data.sel(field="close").transpose("time","asset").astype(float)
    l=xr.where((data.sel(field="is_liquid").transpose("time","asset")==1)&np.isfinite(c)&(c>0),1.0,0.0)
    ma=c.rolling(time=50,min_periods=35).mean(); above=((c>ma)*l).sum("asset")
    n=l.sum("asset"); breadth=xr.where(n>0,above/n,0.0)
    mom=c/c.shift(time=42)-1; r=c/c.shift(time=1)-1; vol=r.rolling(time=28,min_periods=14).std()
    assets=np.sort(c.asset.values.astype(str)); mv=mom.sel(asset=assets).values; lv=l.sel(asset=assets).values
    score=np.zeros_like(mv,float)
    for t in range(mv.shape[0]):
        ids=np.flatnonzero((lv[t]>0)&np.isfinite(mv[t]))
        if ids.size:
            order=ids[np.argsort(mv[t,ids],kind="mergesort")]
            q=max(1,int(np.ceil(ids.size*0.4))); score[t,order[-q:]]=np.maximum(mv[t,order[-q:]],0)
    raw=xr.DataArray(score,dims=("time","asset"),coords={"time":c.time,"asset":assets}).sel(asset=c.asset.values)
    raw=raw/(vol+0.01)*l
    # Continuous breadth gate avoids arbitrary date/regime switches.
    gate=((breadth-0.35)/0.30).clip(min=0.0,max=1.0)
    raw=raw*gate
    gross=raw.sum("asset"); w=xr.where(gross>EPS,raw/gross,0.0)
    return xr.where(w>NAME_CAP,NAME_CAP,w).fillna(0.0).transpose("time","asset")
def strategy(data): return calculate_weights(data)
def load_data(period):
    import qnt.data as qndata
    return qndata.cryptodaily_load_data(tail=max(int(period),LOOKBACK_DAYS))
