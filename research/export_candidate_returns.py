"""Export contest-cost daily returns for one exact Q25 production candidate."""
from __future__ import annotations
import os
from pathlib import Path
import pandas as pd
os.environ.setdefault("API_KEY","default")
import qnt.data as qndata
import qnt.output as qnout
import qnt.stats as qnstats
from research.compare_submission_stability import _weights, START

CANDIDATE=os.environ["CANDIDATE"]
COST=0.04

def main():
    w=_weights(CANDIDATE)
    data=qndata.cryptodaily_load_data(min_date="2015-01-01")
    clean=qnout.clean(w,data,"crypto_daily_long").sel(time=slice(START,None))
    rr=qnstats.calc_relative_return(
        data,clean,slippage_factor=COST,points_per_year=365
    ).sel(time=slice(START,None))
    frame=pd.DataFrame({
        "time":pd.DatetimeIndex(rr.time.values),
        CANDIDATE:rr.values.astype(float),
    })
    path=Path(f"returns_{CANDIDATE}.csv")
    frame.to_csv(path,index=False)
    print(path)
    print(frame.tail().to_string(index=False))

if __name__=="__main__":
    main()
