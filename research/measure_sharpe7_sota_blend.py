"""Fixed 50/50 Sharpe7 + SOTA synthesis measurement.

This is explicitly post-selection synthesis. There is no blend-weight search:
the members are averaged 50/50 and unused gross remains cash.
"""
from __future__ import annotations
import json
import os
import xarray as xr

os.environ.setdefault("API_KEY","default")

import qnt.backtester as qnbt
import qnt.data as qndata
import qnt.output as qnout
import qnt.stats as qnstats
from strategies.generated import ebenezar_20260912_sharpe7_vol2 as sh7
from strategies import q25_sota_meta_ensemble as sota

COMPETITION_TYPE="crypto_daily_long"
START="2016-01-01"
LOOKBACK_DAYS=900


def load_data(period):
    return qndata.cryptodaily_load_data(tail=period)


def strategy(data):
    a=sh7.strategy(data,{"window":7},"base")
    if "time" in a.dims:
        a=a.isel(time=-1,drop=True)
    b=sota.strategy(data)
    a,b=xr.align(a,b,join="outer",fill_value=0.0)
    w=0.5*a+0.5*b
    liquid=data.sel(field="is_liquid").isel(time=-1,drop=True)
    w=xr.where((liquid==1)&(w>0),w,0.0).fillna(0.0)
    # Both members are independently <=25% per name and <=1 gross; the
    # arithmetic average therefore preserves the same cap and unit-gross bound.
    return w


def main():
    result=qnbt.backtest(
        competition_type=COMPETITION_TYPE,
        load_data=load_data,
        lookback_period=LOOKBACK_DAYS,
        start_date=START,
        strategy=strategy,
        analyze=False,
        build_plots=False,
        check_correlation=False,
    )
    if isinstance(result,tuple):
        result=result[0]
    data=qndata.cryptodaily_load_data(min_date="2015-01-01")
    clean=qnout.clean(result,data,COMPETITION_TYPE).sel(time=slice(START,None))
    report={
        "candidate":"q25_sharpe7_sota_equal_blend_v1",
        "evaluation":"full_history_multipass",
        "blend":"0.5_sharpe7_plus_0.5_sota",
        "cost_ladder":{}
    }
    for cost in (0.0,0.04,0.08,0.10,0.12):
        st=qnstats.calc_stat(
            data,clean,slippage_factor=cost,points_per_year=365
        ).sel(time=slice(START,None))
        last=st.isel(time=-1)
        report["cost_ladder"][f"{cost:.2f}"]={
            k:float(last.sel(field=k).item()) for k in
            ("sharpe_ratio","equity","max_drawdown","avg_turnover","volatility")
            if k in last.field.values
        }
    print(json.dumps(report,indent=2,sort_keys=True))


if __name__=="__main__":
    main()
