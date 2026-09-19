"""Full-history multipass measurement for frozen lattice-consensus source."""
from __future__ import annotations
import json, os
os.environ.setdefault("API_KEY","default")
import qnt.backtester as qnbt
import qnt.data as qndata
import qnt.output as qnout
import qnt.stats as qnstats
from strategies.generated import ebenezar_20260912_lattice_consensus as s

def main():
    result=qnbt.backtest(
        competition_type=s.COMPETITION_TYPE,
        load_data=s.load_data,
        lookback_period=s.LOOKBACK_DAYS,
        start_date="2016-01-01",
        strategy=s.strategy,
        analyze=False,
        build_plots=False,
        check_correlation=False,
    )
    weights=result[0] if isinstance(result,tuple) else result
    data=qndata.cryptodaily_load_data(min_date="2015-01-01")
    clean=qnout.clean(weights,data,s.COMPETITION_TYPE)
    clean=clean.sel(time=slice("2016-01-01",None))
    out={"strategy_id":"ebenezar_20260912_lattice_consensus",
         "evaluation":"full_history_multipass","cost_ladder":{}}
    for cost in (0.0,0.04,0.08,0.12):
        st=qnstats.calc_stat(data,clean,slippage_factor=cost,points_per_year=365).sel(time=slice("2016-01-01",None))
        last=st.isel(time=-1)
        out["cost_ladder"][f"{cost:.2f}"]={
            k:float(last.sel(field=k).item()) for k in
            ("sharpe_ratio","equity","max_drawdown","avg_turnover","volatility")
            if k in last.field.values}
    print(json.dumps(out,indent=2,sort_keys=True))
if __name__=="__main__": main()
