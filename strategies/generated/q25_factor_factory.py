"""Frozen factor-factory candidates preregistered in factor_factory_20260922.
No parameter search; Sponsor crypto_daily_long fields only.
"""
import numpy as np
import xarray as xr
COMPETITION_TYPE="crypto_daily_long"; NAME_CAP=.25; EPS=1e-12; LOOKBACK_DAYS=180

def _inputs(data):
 c=data.sel(field="close").transpose("time","asset").astype(float)
 l=xr.where((data.sel(field="is_liquid").transpose("time","asset")==1)&np.isfinite(c)&(c>0),1.,0.)
 r=c/c.shift(time=1)-1
 return c,l,r

def _portfolio(raw,l):
 raw=raw.where(np.isfinite(raw),0).clip(min=0)*l
 raw=raw.rolling(time=3,min_periods=1).mean()*l
 g=raw.sum("asset"); w=xr.where(g>EPS,raw/g,0.)
 return xr.where(w>NAME_CAP,NAME_CAP,w).fillna(0).clip(min=0).transpose("time","asset").reset_coords(drop=True)

def residual_reversal(data):
 c,l,r=_inputs(data); r7=c/c.shift(time=7)-1; r28=c/c.shift(time=28)-1
 x=r28-r28.mean("asset"); y=r7-r7.mean("asset")
 beta=(x*y).mean("asset")/((x*x).mean("asset")+EPS); resid=y-beta*x
 rank=(-resid).rank("asset",pct=True); v=r.rolling(time=21,min_periods=14).std()
 return _portfolio((rank-.5).clip(min=0)/(v+.01),l)

def liquidity_acceleration(data):
 c,l,r=_inputs(data); mom=(c/c.shift(time=28)-1).clip(min=0)
 p14=l.rolling(time=14,min_periods=10).mean(); p56=l.rolling(time=56,min_periods=35).mean()
 accel=(p14-p56).clip(min=0); v=r.rolling(time=21,min_periods=14).std()
 return _portfolio(mom*accel/(v+.01),l)

def crash_resilient_momentum(data):
 c,l,r=_inputs(data); mom=(c/c.shift(time=42)-1).clip(min=0)
 v=r.rolling(time=63,min_periods=42).std(); down=xr.where(r<0,r,0).rolling(time=63,min_periods=42).std()
 resilience=(1-down/(v+EPS)).clip(min=0,max=1); v28=r.rolling(time=28,min_periods=18).std()
 return _portfolio(mom*resilience/(v28+.01),l)

def breadth_dispersion_interaction(data):
 c,l,r=_inputs(data); m=c/c.shift(time=35)-1; rel=m-m.mean("asset")
 breadth=(m>0).mean("asset"); disp=m.std("asset")
 bmed=breadth.rolling(time=63,min_periods=42).median(); dmed=disp.rolling(time=63,min_periods=42).median()
 gate=((breadth-bmed).clip(min=0)/(1-bmed+EPS))*((disp-dmed).clip(min=0)/(disp+dmed+EPS))
 v=r.rolling(time=28,min_periods=18).std()
 return _portfolio(rel.clip(min=0)*gate/(v+.01),l)

FACTORS={"residual_reversal":residual_reversal,"liquidity_acceleration":liquidity_acceleration,"crash_resilient_momentum":crash_resilient_momentum,"breadth_dispersion_interaction":breadth_dispersion_interaction}
