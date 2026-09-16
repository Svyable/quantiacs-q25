"""Post-observation robustness tests for the strongest simple stock-risk state.

This is NOT a clean selection experiment. NDX/SPX commonality-level overlays
were identified after wave-2 measurement. The purpose here is destructive:
1) remove the crypto alpha by applying the state to an equal-weight liquid Q25
   book; and
2) compare current timing to increasingly stale causal versions of the exact
   same state.

If current timing does not dominate stale states, the apparent Sharpe uplift can
be explained by generic de-risking rather than timely cross-asset information.
No result here may be used to retune the commonality lookback or risk mapping.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

DATA_ORIGIN = "2013-01-01"
LAGS = (0, 5, 21, 63, 126, 252)


def _load_wave2():
    path=Path(__file__).parents[1]/"strategies"/"generated"/"omni_cross_asset_wave2_r1.py"
    spec=importlib.util.spec_from_file_location("omni_wave2_robust",path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load wave2")
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


W2=_load_wave2()
FRONTIER=W2.BASE.FRONTIER
R1=W2.BASE.R1
OMNI=W2.BASE.OMNI


def _commonality_risk(stocks: xr.DataArray) -> pd.Series:
    ctx=FRONTIER._stock_context(stocks)
    return R1._robust_unit(FRONTIER._commonality(ctx,126,63)).clip(0.0,1.0)


def _equal_liquid(crypto: xr.DataArray) -> xr.DataArray:
    close=crypto.sel(field="close").transpose("time","asset")
    liquid=crypto.sel(field="is_liquid").transpose("time","asset").fillna(0.0)>0.0
    allowed=liquid & np.isfinite(close) & (close>0.0)
    count=allowed.sum("asset")
    w=xr.where(allowed,1.0/xr.where(count>0,count,1.0),0.0).fillna(0.0)
    return w.transpose("time","asset").rename("weights")


def _fold(rr: xr.DataArray,start:str,end:str|None) -> dict[str,float|int|None]:
    import qnt.stats as qnstats
    x=rr.sel(time=slice(start,end)).fillna(0.0)
    if x.sizes.get("time",0)<10:
        return {"n":int(x.sizes.get("time",0)),"sharpe":None,"equity":None,"max_drawdown":None}
    sh=float(qnstats.calc_sharpe_ratio_annualized(x).isel(time=-1).item())
    r=x.to_pandas().astype(float).fillna(0.0)
    eq=(1.0+r).cumprod(); dd=eq/eq.cummax()-1.0
    return {"n":int(len(r)),"sharpe":sh,"equity":float(eq.iloc[-1]),"max_drawdown":float(dd.min())}


def _eval(crypto:xr.DataArray,w:xr.DataArray) -> dict[str,object]:
    import qnt.stats as qnstats
    rr=qnstats.calc_relative_return(crypto,w)
    scopes={
        "selection_2016_2022":("2016-01-01","2022-12-31"),
        "spent_2023_2024":("2023-01-01","2024-12-31"),
        "diagnostic_2025_plus":("2025-01-01",None),
        "full_is":("2016-01-01",None),
    }
    out={name:_fold(rr,*dates) for name,dates in scopes.items()}
    for year in range(2016,2023):
        out[f"year_{year}"]=_fold(rr,f"{year}-01-01",f"{year}-12-31")
    return out


def run(output:Path) -> dict[str,object]:
    import qnt.data as qndata
    crypto=qndata.cryptodaily_load_data(min_date=DATA_ORIGIN)
    spx=qndata.stocks.load_spx_data(min_date=DATA_ORIGIN)
    ndx=qndata.stocks.load_ndx_data(min_date=DATA_ORIGIN)

    parent=OMNI.calculate_weights({"crypto":crypto,"stocks":spx},mode="base")
    equal=_equal_liquid(crypto)
    carriers={"parent":parent,"equal_liquid":equal}
    states={"spx_commonality":_commonality_risk(spx),"ndx_commonality":_commonality_risk(ndx)}

    metrics:dict[str,object]={}
    for cname,base in carriers.items():
        metrics[f"{cname}__no_overlay"]=_eval(crypto,base)
        for sname,state in states.items():
            for lag in LAGS:
                risk=state.shift(lag) if lag else state
                w=FRONTIER._risk_to_weights(base,risk)
                key=f"{cname}__{sname}__lag{lag}"
                print(f"evaluating {key}",flush=True)
                metrics[key]=_eval(crypto,w)

    # Timing verdict is intentionally simple and fixed: current state should
    # beat every stale causal version on the 2016-2022 selection surface.
    verdicts={}
    for cname in carriers:
        verdicts[cname]={}
        for sname in states:
            current=metrics[f"{cname}__{sname}__lag0"]["selection_2016_2022"]["sharpe"]
            stale={lag:metrics[f"{cname}__{sname}__lag{lag}"]["selection_2016_2022"]["sharpe"] for lag in LAGS if lag}
            verdicts[cname][sname]={
                "current_selection_sharpe":current,
                "stale_selection_sharpe":stale,
                "current_beats_all_stale":bool(current is not None and all(v is not None and current>v for v in stale.values())),
            }

    payload={
        "status":"POST_OBSERVATION_DESTRUCTIVE_ROBUSTNESS_ONLY",
        "may_drive_current_strategy_selection":False,
        "lags":list(LAGS),
        "metrics":metrics,
        "timing_verdicts":verdicts,
    }
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(payload,indent=2,sort_keys=True))
    print(json.dumps(verdicts,indent=2,sort_keys=True))
    return payload


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--output",default="results/omni_timing_robustness/summary.json")
    args=p.parse_args(); run(Path(args.output))


if __name__=="__main__":
    main()
