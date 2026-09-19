"""Destructive controls for the frozen lattice-consensus candidate."""
from __future__ import annotations
import json, os
import numpy as np
import xarray as xr
os.environ.setdefault("API_KEY","default")
import qnt.data as qndata
import qnt.output as qnout
import qnt.stats as qnstats
from strategies.generated import ebenezar_20260912_lattice_consensus as s

def _parts(data):
    c,l,r=s._base(data)
    v=s._std(r,21,10)
    sharpe=np.sqrt(365.0)*s._sma(r,7,5)/(v+s.EPS)
    sma18=s._sma(c,18,10); sma50=s._sma(c,50,25)
    trend=sma18/(sma50+s.EPS)-1.0
    mom=c/c.shift(time=14)-1.0
    peak=s._max(c,42,20); dd=c/(peak+s.EPS)-1.0
    ms=s._mean(sharpe,l); mv=s._mean(v,l)
    support=(xr.where(trend>0,1.0,0.0)+xr.where(sharpe>ms,1.0,0.0)+
             xr.where(mom>0,1.0,0.0)+xr.where(v<1.25*mv,1.0,0.0)+
             xr.where(dd>-0.25,1.0,0.0))
    quality=(xr.where(sharpe>ms,sharpe-ms,0.0)+
             2*xr.where(trend>0,trend,0.0)+
             xr.where(mom>0,mom,0.0))*(support/5.0)
    return l,v,trend,support,quality

def control(data,mode):
    l,v,trend,support,quality=_parts(data)
    if mode=="no_consensus_threshold":
        raw=xr.where(quality>0,quality/(v+0.015),0.0)*l
    elif mode=="consensus_membership_only":
        raw=xr.where(support>=4.0,1.0/(v+0.015),0.0)*l
    elif mode=="trend_only":
        raw=xr.where(trend>0,trend/(v+0.015),0.0)*l
    else:
        raise ValueError(mode)
    raw=s._sma(raw,5,1)*l
    return s._alloc(raw,l)

def metric(data,w):
    clean=qnout.clean(w,data,s.COMPETITION_TYPE)
    st=qnstats.calc_stat(data,clean.sel(time=slice("2016-01-01",None)),
        slippage_factor=0.04,points_per_year=365).sel(time=slice("2016-01-01",None))
    last=st.isel(time=-1)
    return {k:float(last.sel(field=k).item()) for k in
        ("sharpe_ratio","equity","max_drawdown","avg_turnover","volatility")
        if k in last.field.values}

def main():
    data=qndata.cryptodaily_load_data(min_date="2015-01-01")
    out={"cost_fraction_atr":0.04,"base":metric(data,s.strategy(data))}
    for mode in ("no_consensus_threshold","consensus_membership_only","trend_only"):
        out[mode]=metric(data,control(data,mode))
    print(json.dumps(out,indent=2,sort_keys=True))
if __name__=="__main__": main()
