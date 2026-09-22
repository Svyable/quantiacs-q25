"""Full-multipass hardening controls for frozen sharpe3_vol_guard.

MODE=base reproduces the frozen source exactly. Other modes deliberately remove
one mechanism while preserving the same sponsor data, long-only constraint,
365-day lookback, and 25% name cap. These controls do not retune the base.
"""
from __future__ import annotations

import json
import os
import numpy as np
import xarray as xr

os.environ.setdefault("API_KEY","default")

import qnt.backtester as qnbt
import qnt.data as qndata
import qnt.output as qnout
import qnt.stats as qnstats
from strategies.generated import ebenezar_20260912_sharpe3_vol_guard as s

START="2016-01-01"
MODE=os.environ.get("MODE","base")


def control_strategy(data):
    if MODE=="base":
        out=s.strategy(data,{"window":3},"base")
        return out.isel(time=-1,drop=True) if "time" in out.dims else out

    close, liquid=s._close_liquid(data)
    r=s._returns(close)
    mu3=s._sma(r,3,3)
    vol21=s._std(r,21,10)
    s3=np.sqrt(365.0)*mu3/(vol21+s.EPS)
    mom7=close/close.shift(time=7)-1.0
    trend34=close/(s._sma(close,34,20)+s.EPS)-1.0
    mean=s._liquid_cs_mean(s3,liquid)
    sd=s._liquid_cs_std(s3,liquid)
    hurdle=mean+0.10*sd
    conviction=xr.where(s3>hurdle,s3-hurdle,0.0)

    if MODE=="no_confirmation_gates":
        gate=vol21>0.0
        raw=xr.where(gate,conviction/(vol21+0.01),0.0)*liquid
    elif MODE=="plain_3d_momentum":
        cs_mean=s._liquid_cs_mean(mu3,liquid)
        simple=xr.where(mu3>cs_mean,mu3-cs_mean,0.0)
        gate=(mom7>0.0)&(trend34>0.0)&(vol21>0.0)
        raw=xr.where(gate,simple/(vol21+0.01),0.0)*liquid
    elif MODE=="no_inverse_vol":
        gate=(mom7>0.0)&(trend34>0.0)&(vol21>0.0)
        raw=xr.where(gate,conviction,0.0)*liquid
    else:
        raise ValueError(MODE)

    raw=s._sma(raw,2,1)*liquid
    out=s._allocate(raw,liquid)
    return out.isel(time=-1,drop=True)


def load_data(period):
    return qndata.cryptodaily_load_data(tail=period)


def main():
    result=qnbt.backtest(
        competition_type=s.COMPETITION_TYPE,
        load_data=load_data,
        lookback_period=s.LOOKBACK_DAYS,
        start_date=START,
        strategy=control_strategy,
        analyze=False,
        build_plots=False,
        check_correlation=False,
    )
    if isinstance(result,tuple):
        result=result[0]
    data=qndata.cryptodaily_load_data(min_date="2015-01-01")
    clean=qnout.clean(result,data,s.COMPETITION_TYPE).sel(time=slice(START,None))
    costs=(0.0,0.04,0.08,0.10,0.12) if MODE=="base" else (0.04,)
    report={"candidate":"sharpe3_vol_guard","mode":MODE,"evaluation":"full_history_multipass","cost_ladder":{}}
    for cost in costs:
        st=qnstats.calc_stat(data,clean,slippage_factor=cost,points_per_year=365).sel(time=slice(START,None))
        last=st.isel(time=-1)
        report["cost_ladder"][f"{cost:.2f}"]={
            k:float(last.sel(field=k).item()) for k in
            ("sharpe_ratio","equity","max_drawdown","avg_turnover","volatility")
            if k in last.field.values
        }
    print(json.dumps(report,indent=2,sort_keys=True))


if __name__=="__main__":
    main()
