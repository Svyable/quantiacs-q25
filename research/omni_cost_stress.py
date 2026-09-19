"""Exact Quantiacs cost/fold stress for observed OMNI cross-asset overlays.

Post-observation robustness only: candidate identities are fixed from prior
measurements and cannot be retuned from this result. Uses the repository's
QuantiacsEvaluator, official cleaner, chronological research/dev folds and
configured 4%/8%/12% ATR slippage ladder.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DATA_ORIGIN="2013-01-01"


def _load(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


W2=_load(ROOT/"strategies/generated/omni_cross_asset_wave2_r1.py","omni_w2_cost")
FRONTIER=W2.BASE.FRONTIER
R1=W2.BASE.R1
OMNI=W2.BASE.OMNI
BENCH=_load(ROOT/"research/benchmark.py","omni_benchmark_cost")


def _commonality(stocks):
    ctx=FRONTIER._stock_context(stocks)
    return R1._robust_unit(FRONTIER._commonality(ctx,126,63)).clip(0.0,1.0)


def _volterm(stocks):
    ctx=FRONTIER._stock_context(stocks)
    market=ctx["market"]
    vol21=market.rolling(21,min_periods=14).std(ddof=1)
    vol126=market.rolling(126,min_periods=63).std(ddof=1)
    return R1._robust_unit(np.log((vol21+1e-12)/(vol126+1e-12))).clip(0.0,1.0)


def run(output:Path):
    import qnt.data as qndata
    crypto=qndata.cryptodaily_load_data(min_date=DATA_ORIGIN)
    spx=qndata.stocks.load_spx_data(min_date=DATA_ORIGIN)
    ndx=qndata.stocks.load_ndx_data(min_date=DATA_ORIGIN)

    base=OMNI.calculate_weights({"crypto":crypto,"stocks":spx},mode="base")
    candidates={
        "base":base,
        "omni_v1_ungated_spx":OMNI.calculate_weights({"crypto":crypto,"stocks":spx},mode="ungated"),
        "commonality_spx":FRONTIER._risk_to_weights(base,_commonality(spx)),
        "commonality_ndx":FRONTIER._risk_to_weights(base,_commonality(ndx)),
        "volterm_spx":FRONTIER._risk_to_weights(base,_volterm(spx)),
        "volterm_ndx":FRONTIER._risk_to_weights(base,_volterm(ndx)),
        "tail_spx":FRONTIER._risk_to_weights(base,FRONTIER._tail_dependence(FRONTIER._stock_context(spx))["primary"]),
        "tail_ndx":FRONTIER._risk_to_weights(base,FRONTIER._tail_dependence(FRONTIER._stock_context(ndx))["primary"]),
    }

    folds,costs=BENCH.policy()
    evaluator=BENCH.QuantiacsEvaluator(crypto)
    results={}
    for name,w in candidates.items():
        print(f"exact cost stress {name}",flush=True)
        metrics,_=evaluator.evaluate(w,folds,costs)
        robust=BENCH.selection_score(metrics)
        results[name]={"robust_selection_score":robust,"metrics":metrics}
        print(name,"robust",robust,flush=True)

    ranking=sorted(((v["robust_selection_score"],k) for k,v in results.items() if v["robust_selection_score"] is not None),reverse=True)
    payload={
        "status":"POST_OBSERVATION_EXACT_COST_ROBUSTNESS_ONLY",
        "may_drive_current_strategy_selection":False,
        "cost_ladder":costs,
        "folds":folds,
        "results":results,
        "ranking_by_worst_research_dev_cost_sharpe":ranking,
    }
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(payload,indent=2,sort_keys=True))
    print("\n=== ROBUST WORST-FOLD/COST SHARPE ===")
    for score,name in ranking:
        print(f"{name:28s} {score:.6f}")
    return payload


def main():
    p=argparse.ArgumentParser(); p.add_argument("--output",default="results/omni_cost_stress/summary.json")
    a=p.parse_args(); run(Path(a.output))


if __name__=="__main__":
    main()
