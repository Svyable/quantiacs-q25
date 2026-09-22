"""Preregistered residual-momentum candidate: cross-sectional market-neutral signal, long-only portfolio."""
import numpy as np
import xarray as xr
COMPETITION_TYPE="crypto_daily_long"; STRATEGY_ID="q25_residual_momentum_v1"; LOOKBACK_DAYS=180; NAME_CAP=0.25; EPS=1e-12

def _inputs(data):
    c=data.sel(field="close").transpose("time","asset").astype(float)
    l=xr.where((data.sel(field="is_liquid").transpose("time","asset")==1)&np.isfinite(c)&(c>0),1.0,0.0)
    return c,l
def _cs_mean(x,l):
    z=xr.where(np.isfinite(x),x,0.0)*l; n=l.sum("asset")
    return xr.where(n>0,z.sum("asset")/n,0.0)
def _rank_positive(x,l):
    assets=np.sort(x.asset.values.astype(str)); xx=x.sel(asset=assets); ll=l.sel(asset=assets)
    v=xx.values; ok=(ll.values>0)&np.isfinite(v); out=np.zeros_like(v,float)
    for t in range(v.shape[0]):
        ids=np.flatnonzero(ok[t])
        if ids.size:
            order=ids[np.argsort(v[t,ids],kind="mergesort")]
            ranks=np.empty(ids.size); ranks[np.argsort(order)]=np.arange(1,ids.size+1)/ids.size
            out[t,ids]=np.maximum(ranks-0.5,0.0)
    return xr.DataArray(out,dims=xx.dims,coords=xx.coords).sel(asset=x.asset.values)
def calculate_weights(data):
    c,l=_inputs(data); r=c/c.shift(time=1)-1
    m21=c/c.shift(time=21)-1; m63=c/c.shift(time=63)-1
    residual=0.65*(m21-_cs_mean(m21,l))+0.35*(m63-_cs_mean(m63,l))
    vol=r.rolling(time=28,min_periods=14).std()
    raw=_rank_positive(residual,l)/(vol+0.01)*l
    raw=raw.rolling(time=3,min_periods=1).mean()*l
    gross=raw.sum("asset"); w=xr.where(gross>EPS,raw/gross,0.0)
    return xr.where(w>NAME_CAP,NAME_CAP,w).fillna(0.0).transpose("time","asset")
def strategy(data): return calculate_weights(data)
def load_data(period):
    import qnt.data as qndata
    return qndata.cryptodaily_load_data(tail=max(int(period),LOOKBACK_DAYS))
