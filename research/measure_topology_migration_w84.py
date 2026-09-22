"""Authoritative current full-history multipass for frozen topology_migration_w84."""
from __future__ import annotations
import json, os
os.environ.setdefault("API_KEY","default")
import qnt.backtester as qnbt
import qnt.data as qndata
import qnt.output as qnout
import qnt.stats as qnstats
from strategies.generated import frontier_20260910b_topology_migration as s

START="2016-01-01"
PARAMS={"window":84,"top_k":5}

def frozen_strategy(data):
    out=s.strategy(data,PARAMS,"base")
    return out.isel(time=-1,drop=True) if "time" in out.dims else out

def main():
    result=qnbt.backtest(
        competition_type=s.COMPETITION_TYPE,
        load_data=s.load_data,
        lookback_period=s.LOOKBACK_DAYS,
        start_date=START,
        strategy=frozen_strategy,
        analyze=False,
        build_plots=False,
        check_correlation=False,
    )
    if isinstance(result,tuple): result=result[0]
    data=qndata.cryptodaily_load_data(min_date="2015-01-01")
    clean=qnout.clean(result,data,s.COMPETITION_TYPE).sel(time=slice(START,None))
    report={"candidate":"topology_migration_w84","evaluation":"full_history_multipass","params":PARAMS,"cost_ladder":{}}
    for cost in (0.0,0.04,0.08,0.10,0.12):
        st=qnstats.calc_stat(data,clean,slippage_factor=cost,points_per_year=365).sel(time=slice(START,None))
        last=st.isel(time=-1)
        report["cost_ladder"][f"{cost:.2f}"]={
            k:float(last.sel(field=k).item()) for k in
            ("sharpe_ratio","equity","max_drawdown","avg_turnover","volatility")
            if k in last.field.values
        }
    print(json.dumps(report,indent=2,sort_keys=True))

if __name__=="__main__": main()
