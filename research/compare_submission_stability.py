"""Stability diagnostics for exact Q25 production candidates.

Uses the exact production mode for each candidate, then calculates contest-cost
daily returns and regime/stability summaries. This is diagnostics only; no
candidate parameters are changed from the measured submission artifacts.
"""
from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

os.environ.setdefault("API_KEY","default")

import qnt.backtester as qnbt
import qnt.data as qndata
import qnt.output as qnout
import qnt.stats as qnstats

ROOT=Path(__file__).resolve().parents[1]
START="2016-01-01"
COST=0.04


def _load(path: str, name: str):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _weights(candidate: str):
    if candidate=="lattice":
        m=_load("submissions/q25_lattice_consensus_multipass.py","lattice_submission")
        result=qnbt.backtest(
            competition_type=m.COMPETITION_TYPE,
            load_data=m.load_data,
            lookback_period=m.LOOKBACK_DAYS,
            start_date=START,
            strategy=m.strategy,
            analyze=False,
            build_plots=False,
            check_correlation=False,
        )
        return result[0] if isinstance(result,tuple) else result
    if candidate=="sota":
        m=_load("submissions/q25_sota_meta_ensemble_multipass.py","sota_submission")
        result=qnbt.backtest(
            competition_type=m.COMPETITION_TYPE,
            load_data=m.load_data,
            lookback_period=m.LOOKBACK_DAYS,
            start_date=START,
            strategy=m.strategy,
            analyze=False,
            build_plots=False,
            check_correlation=False,
        )
        return result[0] if isinstance(result,tuple) else result
    if candidate=="hit126":
        m=_load("submissions/q25_hit126_consistency_singlepass.py","hit126_submission")
        data=qndata.cryptodaily_load_data(min_date="2015-01-01")
        return m.compute_weights(data)
    if candidate=="sharpe3":
        m=_load("submissions/q25_sharpe3_vol_guard_multipass.py","sharpe3_submission")
        result=qnbt.backtest(
            competition_type=m.COMPETITION_TYPE,
            load_data=m.load_data,
            lookback_period=m.LOOKBACK_DAYS,
            start_date=START,
            strategy=lambda d: m.strategy(d,{"window":3},"base),
            analyze=False,
            build_plots=False,
            check_correlation=False,
        )
        return result[0] if isinstance(result,tuple) else result
    raise ValueError(candidate)


def _sharpe(rr):
    if rr.sizes.get("time",0)<2:
        return float("nan")
    out=qnstats.calc_sharpe_ratio_annualized(
        rr,
        min_periods=2,
        points_per_year=365,
        mean_estimator="arithmetic",
    )
    return float(out.isel(time=-1).item())


def main():
    candidate=os.environ["CANDIDATE"]
    weights=_weights(candidate)
    data=qndata.cryptodaily_load_data(min_date="2015-01-01")
    clean=qnout.clean(weights,data,"crypto_daily_long").sel(time=slice(START,None))
    rr=qnstats.calc_relative_return(
        data,clean,slippage_factor=COST,points_per_year=365
    ).sel(time=slice(START,None))

    years={}
    idx=pd.DatetimeIndex(rr.time.values)
    for year in sorted(set(idx.year)):
        sub=rr.sel(time=idx.year==year)
        values=np.asarray(sub.values,dtype=float)
        values=values[np.isfinite(values)]
        if len(values)<2:
            continue
        equity=float(np.prod(1.0+values))
        years[str(year)]={
            "days":int(len(values)),
            "sharpe":_sharpe(sub),
            "return":equity-1.0,
        }

    rolling=qnstats.calc_sharpe_ratio_annualized(
        rr,
        max_periods=365,
        min_periods=180,
        points_per_year=365,
        mean_estimator="arithmetic",
    )
    rv=np.asarray(rolling.values,dtype=float)
    rv=rv[np.isfinite(rv)]

    last365=rr.isel(time=slice(max(0,rr.sizes["time"]-365),None))
    annual_sharpes=[v["sharpe"] for v in years.values() if np.isfinite(v["sharpe"])]
    annual_returns=[v["return"] for v in years.values() if np.isfinite(v["return"])]

    report={
        "candidate":candidate,
        "mode":{"lattice":"multipass_365","sota":"multipass_900","hit126":"singlepass_parity_proven","sharpe3":"multipass_365","sharpe7":"multipass_365","residual":"multipass_365"}[candidate],
        "cost_fraction_atr":COST,
        "calendar_years":years,
        "stability":{
            "positive_return_year_fraction":float(np.mean(np.asarray(annual_returns)>0)),
            "positive_sharpe_year_fraction":float(np.mean(np.asarray(annual_sharpes)>0)),
            "median_calendar_year_sharpe":float(np.median(annual_sharpes)),
            "worst_calendar_year_sharpe":float(np.min(annual_sharpes)),
            "last_365d_sharpe":_sharpe(last365),
            "rolling_365d_sharpe_q10":float(np.quantile(rv,0.10)) if len(rv) else float("nan"),
            "rolling_365d_sharpe_median":float(np.median(rv)) if len(rv) else float("nan"),
            "rolling_365d_sharpe_q90":float(np.quantile(rv,0.90)) if len(rv) else float("nan"),
        }
    }
    print(json.dumps(report,indent=2,sort_keys=True))


if __name__=="__main__":
    main()
