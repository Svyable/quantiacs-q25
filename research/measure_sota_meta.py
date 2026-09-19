"""Measure the pre-existing q25_sota_meta_ensemble_v1 without changing it."""
from __future__ import annotations
import json, os
os.environ.setdefault("API_KEY","default")
import qnt.backtester as qnbt
import qnt.data as qndata
import qnt.output as qnout
import qnt.stats as qnstats
from strategies import q25_sota_meta_ensemble as s

def main():
    weights=qnbt.backtest(
        competition_type=s.COMPETITION_TYPE,
        load_data=s.load_data,
        lookback_period=s.LOOKBACK_DAYS,
        start_date=s.RESEARCH_START,
        strategy=s.strategy,
        analyze=False,
        check_correlation=False,
    )
    data=qndata.cryptodaily_load_data(min_date="2015-01-01")
    weights=qnout.clean(weights,data,s.COMPETITION_TYPE)
    weights=weights.sel(time=slice(s.RESEARCH_START,None))
    out={"strategy_id":s.STRATEGY_ID,"evaluation":"multipass","cost_ladder":{}}
    for cost in (0.0,0.04,0.08,0.12):
        st=qnstats.calc_stat(data,weights,slippage_factor=cost,points_per_year=365).sel(time=slice(s.RESEARCH_START,None))
        last=st.isel(time=-1)
        out["cost_ladder"][f"{cost:.2f}"]={
            k:float(last.sel(field=k).item()) for k in
            ("sharpe_ratio","equity","max_drawdown","avg_turnover","volatility")
            if k in last.field.values
        }
    print(json.dumps(out,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
