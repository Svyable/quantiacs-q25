"""Measure the pre-existing lattice-consensus source without modifying it."""
from __future__ import annotations
import json, os
os.environ.setdefault("API_KEY","default")
import qnt.data as qndata
import qnt.output as qnout
import qnt.stats as qnstats
from strategies.generated import ebenezar_20260912_lattice_consensus as s

def main():
    data=qndata.cryptodaily_load_data(min_date="2015-01-01")
    weights=s.strategy(data)
    clean=qnout.clean(weights,data,s.COMPETITION_TYPE)
    ins=clean.sel(time=slice("2016-01-01",None))
    out={"strategy_id":"ebenezar_20260912_lattice_consensus","evaluation":"single_pass","cost_ladder":{}}
    for cost in (0.0,0.04,0.08,0.12):
        st=qnstats.calc_stat(data,ins,slippage_factor=cost,points_per_year=365).sel(time=slice("2016-01-01",None))
        last=st.isel(time=-1)
        out["cost_ladder"][f"{cost:.2f}"]={
            k:float(last.sel(field=k).item()) for k in
            ("sharpe_ratio","equity","max_drawdown","avg_turnover","volatility")
            if k in last.field.values
        }
    print(json.dumps(out,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
