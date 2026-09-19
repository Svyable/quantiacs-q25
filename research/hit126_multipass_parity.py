"""Real-data single-pass vs Quantiacs multipass parity for hit126 candidate."""
from __future__ import annotations
import json, os, time
os.environ.setdefault("API_KEY","default")
import numpy as np
import qnt.backtester as qnbt
import qnt.data as qndata
import qnt.output as qnout
from strategies.generated import q25_deadline_hit126_consistency as s

PARITY_START="2026-06-01"

def main():
    t0=time.perf_counter()
    mp=qnbt.backtest(
        competition_type=s.COMPETITION_TYPE,
        load_data=s.load_data,
        lookback_period=s.LOOKBACK_DAYS,
        start_date=PARITY_START,
        strategy=s.strategy,
        analyze=False,
        build_plots=False,
        check_correlation=False,
    )
    multipass_seconds=time.perf_counter()-t0

    data=qndata.cryptodaily_load_data(min_date="2015-01-01")
    t1=time.perf_counter()
    sp=s.compute_weights(data)
    singlepass_seconds=time.perf_counter()-t1
    sp=qnout.clean(sp,data,s.COMPETITION_TYPE)

    common=np.intersect1d(mp.time.values,sp.time.values)
    if len(common)==0:
        raise RuntimeError("no common dates between multipass and single-pass")
    a=mp.sel(time=common).transpose("time","asset")
    b=sp.sel(time=common,asset=a.asset.values).transpose("time","asset")
    diff=np.nanmax(np.abs(a.values-b.values))
    report={
        "strategy_id":s.STRATEGY_ID,
        "parity_start":PARITY_START,
        "common_days":int(len(common)),
        "max_abs_weight_difference":float(diff),
        "singlepass_compute_seconds":float(singlepass_seconds),
        "multipass_wall_seconds":float(multipass_seconds),
        "status":"PASS" if diff<=1e-12 else "FAIL",
    }
    print(json.dumps(report,indent=2,sort_keys=True))
    if diff>1e-12:
        raise AssertionError(f"single/multipass max abs diff {diff}")

if __name__=="__main__":
    main()
