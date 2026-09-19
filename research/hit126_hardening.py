"""Destructive-control evaluation for q25_deadline_hit126_consistency_v1.

This is research instrumentation, not a submission strategy. It keeps the
candidate's schedule, liquidity rules, inverse-risk sizing, cap, and cost
model fixed while destroying one mechanism component at a time.
"""
from __future__ import annotations
import json, os
import numpy as np
import pandas as pd
import xarray as xr
from strategies.generated import q25_deadline_hit126_consistency as base

EPS=1e-12

def _variant_signals(data, mode):
    close=base._frame(data,"close")
    liquid=base._frame(data,"is_liquid").fillna(0.0)>0.0
    tradable=liquid & close.notna() & (close>0.0)
    log_close=np.log(close.where(close>0.0))
    ret=log_close.diff()
    positive=(ret>0.0).astype(float).where(ret.notna())
    hit=positive.rolling(base.HIT_WINDOW,min_periods=base.HIT_MIN).mean()
    displacement=log_close-log_close.shift(base.HIT_WINDOW)
    risk=ret.rolling(base.RISK_WINDOW,min_periods=base.RISK_MIN).std(ddof=1)

    if mode=="displacement_only":
        score=displacement.where(displacement>0.0)
    elif mode=="no_displacement_confirmation":
        score=(hit-0.50)
    elif mode=="negative_hit_rate":
        score=(0.50-hit).where(displacement<0.0)
    else:
        raise ValueError(mode)
    return tradable,score,risk

def compute_control(data, mode):
    tradable,score,risk=_variant_signals(data,mode)
    dates=pd.DatetimeIndex(score.index)
    rebalance=pd.Series(dates.dayofweek==0,index=dates)
    target=pd.DataFrame(np.nan,index=dates,columns=score.columns,dtype=float)
    for dt in dates[rebalance.to_numpy()]:
        s=score.loc[dt].replace([np.inf,-np.inf],np.nan)
        valid=tradable.loc[dt].fillna(False)&s.notna()&(s>0.0)
        canonical=sorted(s.index.astype(str))
        s_c=s.reindex(canonical); valid_c=valid.reindex(canonical)
        rank= s_c.where(valid_c).rank(ascending=False,method="first").reindex(s.index)
        selected=valid&(rank<=base.TOP_K)
        if not bool(selected.any()):
            target.loc[dt]=0.0; continue
        # Keep sizing invariant to the base: bounded score conviction + inverse risk.
        if mode=="displacement_only":
            pct=s.where(selected).rank(pct=True,method="average")
            conviction=(0.5+pct).where(selected,0.0)
        else:
            conviction=(0.5+s.clip(lower=0.0)/0.15).clip(0.5,1.5)
        raw=(conviction/(risk.loc[dt]+EPS)).where(selected,0.0)
        target.loc[dt]=base._waterfill(raw)
    weights=target.ffill().fillna(0.0).where(tradable,0.0)
    held=pd.Series(False,index=weights.columns)
    active=pd.DataFrame(False,index=dates,columns=weights.columns)
    for i,dt in enumerate(dates):
        if bool(rebalance.iloc[i]): held=weights.loc[dt]>0.0
        held=held&tradable.loc[dt].fillna(False)
        active.loc[dt]=held
    weights=weights.where(active,0.0).clip(lower=0.0,upper=base.NAME_CAP)
    gross=weights.sum(axis=1); over=gross>1.0+1e-12
    if bool(over.any()): weights.loc[over]=weights.loc[over].div(gross.loc[over],axis=0)
    return xr.DataArray(weights.to_numpy(float),dims=("time","asset"),
        coords={"time":weights.index.to_numpy(),"asset":weights.columns.to_numpy()}).fillna(0.0)

def metric(data, weights, cost=0.04):
    import qnt.output as qnout, qnt.stats as qnstats
    clean=qnout.clean(weights,data,base.COMPETITION_TYPE)
    stats=qnstats.calc_stat(data,clean.sel(time=slice(base.IN_SAMPLE_START,None)),
        slippage_factor=cost,points_per_year=365).sel(time=slice(base.IN_SAMPLE_START,None))
    last=stats.isel(time=-1)
    return {k:float(last.sel(field=k).item()) for k in
        ("sharpe_ratio","equity","max_drawdown","avg_turnover","volatility")}

def main():
    os.environ.setdefault("API_KEY","default")
    import qnt.data as qndata
    data=qndata.cryptodaily_load_data(min_date="2015-01-01")
    out={"cost_fraction_atr":0.04,"base":metric(data,base.compute_weights(data))}
    for mode in ("displacement_only","no_displacement_confirmation","negative_hit_rate"):
        out[mode]=metric(data,compute_control(data,mode))
    print(json.dumps(out,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
