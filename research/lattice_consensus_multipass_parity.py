"""Real-data single/multipass parity for frozen lattice-consensus source."""
from __future__ import annotations
import json, os, time
import numpy as np
os.environ.setdefault("API_KEY","default")
import qnt.backtester as qnbt
import qnt.data as qndata
import qnt.output as qnout
from strategies.generated import ebenezar_20260912_lattice_consensus as s
START="2026-06-01"

def main():
    t0=time.perf_counter()
    mp=qnbt.backtest(
        competition_type=s.COMPETITION_TYPE,
        load_data=s.load_data,
        lookback_period=365,
        start_date=START,
        strategy=s.strategy,
        analyze=False,
        build_plots=False,
        check_correlation=False,
    )
    if isinstance(mp,tuple): mp=mp[0]
    mt=time.perf_counter()-t0
    data=qndata.cryptodaily_load_data(min_date="2015-01-01")
    t1=time.perf_counter(); sp=s.strategy(data); st=time.perf_counter()-t1
    sp=qnout.clean(sp,data,s.COMPETITION_TYPE)
    common=np.intersect1d(mp.time.values,sp.time.values)
    a=mp.sel(time=common).transpose("time","asset")
    b=sp.sel(time=common,asset=a.asset.values).transpose("time","asset")
    diff=float(np.nanmax(np.abs(a.values-b.values)))
    out={"strategy_id":"ebenezar_20260912_lattice_consensus","common_days":int(len(common)),
         "max_abs_weight_difference":diff,"singlepass_compute_seconds":float(st),
         "multipass_wall_seconds":float(mt),"status":"PASS" if diff<=1e-12 else "FAIL"}
    print(json.dumps(out,indent=2,sort_keys=True))
    if diff>1e-12: raise AssertionError(diff)
if __name__=="__main__": main()
