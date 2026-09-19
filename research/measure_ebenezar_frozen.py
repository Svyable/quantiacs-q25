"""Authoritative full-history multipass measurement for frozen Ebenezar profiles.

PROFILE must be one of the pre-existing preregistered sources below. This file
does not alter their formulas or parameters; it only adapts them to the
Quantiacs multipass evaluator and reports the contest cost ladder.
"""
from __future__ import annotations
import importlib
import json
import os

os.environ.setdefault("API_KEY","default")

import qnt.backtester as qnbt
import qnt.data as qndata
import qnt.output as qnout
import qnt.stats as qnstats

PROFILES = {
    "sharpe3_vol_guard": ("ebenezar_20260912_sharpe3_vol_guard", 3),
    "sharpe7_vol2": ("ebenezar_20260912_sharpe7_vol2", 7),
    "dual_sharpe_classifier": ("ebenezar_20260912_dual_sharpe_classifier", 7),
    "sharpe_acceleration": ("ebenezar_20260912_sharpe_acceleration", 3),
    "residual_sharpe": ("ebenezar_20260912_residual_sharpe", 7),
    "sharpe_pullback_reentry": ("ebenezar_20260912_sharpe_pullback_reentry", 21),
}
START="2016-01-01"
LOOKBACK=365

def main():
    key=os.environ["PROFILE"]
    module_name,window=PROFILES[key]
    m=importlib.import_module(f"strategies.generated.{module_name}")

    def frozen_strategy(data):
        out=m.strategy(data,{"window":window},"base")
        if "time" in out.dims:
            out=out.isel(time=-1,drop=True)
        return out

    def load_data(period):
        return qndata.cryptodaily_load_data(tail=period)

    result=qnbt.backtest(
        competition_type="crypto_daily_long",
        load_data=load_data,
        lookback_period=LOOKBACK,
        start_date=START,
        strategy=frozen_strategy,
        analyze=False,
        build_plots=False,
        check_correlation=False,
    )
    if isinstance(result,tuple):
        result=result[0]
    data=qndata.cryptodaily_load_data(min_date="2015-01-01")
    clean=qnout.clean(result,data,"crypto_daily_long").sel(time=slice(START,None))
    report={"profile":key,"source":module_name,"window":window,
            "evaluation":"full_history_multipass","cost_ladder":{}}
    for cost in (0.0,0.04,0.08,0.12):
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
