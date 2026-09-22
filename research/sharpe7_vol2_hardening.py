"""Full-multipass hardening controls for frozen sharpe7_vol2.

MODE=base reproduces the frozen source. Other modes remove one mechanism while
holding sponsor data, long-only rules, lookback, and cap fixed.
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
from strategies.generated import ebenezar_20260912_sharpe7_vol2 as s

START="2016-01-01"
MODE=os.environ.get("MODE","base")


def control_strategy(data):
    if MODE=="base":
        out=s.strategy(data,{"window":7},"base")
        return out.isel(time=-1,drop=True) if "time" in out.dims else out

    close,liquid=s._close_liquid(data)
    r=s._returns(close)
    mu7=s._sma(r,7,5)
    vol14=s._std(r,14,7)
    s7=np.sqrt(365.0)*mu7/(vol14+s.EPS)
    sma12=s._sma(close,12,8)
    sma48=s._sma(close,48,24)
    mom14=close/close.shift(time=14)-1.0
    peak30=s._max(close,30,15)
    dd30=close/(peak30+s.EPS)-1.0
    mean=s._liquid_cs_mean(s7,liquid)
    sd=s._liquid_cs_std(s7,liquid)
    hurdle=mean+0.20*sd
    quality=xr.where(s7>hurdle,s7-hurdle,0.0)

    if MODE=="no_confirmation_gates":
        gate=vol14>0.0
        raw=xr.where(gate,(quality.clip(min=0.0)**1.25)/(vol14+0.015),0.0)*liquid
    elif MODE=="plain_7d_momentum":
        cs_mean=s._liquid_cs_mean(mu7,liquid)
        simple=xr.where(mu7>cs_mean,mu7-cs_mean,0.0)
        gate=(sma12>sma48)&(mom14>0.0)&(dd30>-0.22)&(vol14>0.0)
        raw=xr.where(gate,simple/(vol14+0.015),0.0)*liquid
    elif MODE=="no_inverse_vol":
        gate=(sma12>sma48)&(mom14>0.0)&(dd30>-0.22)&(vol14>0.0)
        raw=xr.where(gate,quality.clip(min=0.0)**1.25,0.0)*liquid
    else:
        raise ValueError(MODE)

    raw=s._sma(raw,3,1)*liquid
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
    report={"candidate":"sharpe7_vol2","mode":MODE,"evaluation":"full_history_multipass","cost_ladder":{}}
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
