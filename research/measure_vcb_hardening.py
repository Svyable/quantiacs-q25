"""Frozen development-only hardening measurement for VCB; never loads post-2022 data."""
from __future__ import annotations
import importlib, json, os
from pathlib import Path
import numpy as np, xarray as xr
os.environ.setdefault("API_KEY","default")
import qnt.data as qndata
from research.benchmark import QuantiacsEvaluator, check_causality, check_weights, panel_hash, validate_panel
ROOT=Path(__file__).resolve().parents[1]
START="2015-01-01"; EVAL_START="2016-01-01"; END="2022-12-31"
FOLDS=[{"id":"research_2016_2020","start":"2016-01-01","end":"2020-12-31"},{"id":"development_2021_2022","start":"2021-01-01","end":END}]
COSTS=[0.04,0.08,0.12]

def _permute(w,data):
 l=xr.where(data.sel(field="is_liquid").transpose("time","asset")==1,1.,0.)
 return (w.roll(asset=1,roll_coords=False)*l).fillna(0).clip(min=0).transpose("time","asset").reset_coords(drop=True)

def _metrics(e,w):
 m,_=e.evaluate(w,FOLDS,COSTS); return m

def main():
 data=qndata.cryptodaily_load_data(min_date=START,max_date=END).sel(time=slice(START,END))
 validate_panel(data,EVAL_START,END)
 if str(data.time.values[-1])[:10]>END: raise AssertionError("holdout entered hardening")
 mod=importlib.import_module("strategies.generated.q25_volatility_contraction_breakout")
 with xr.set_options(use_bottleneck=False): w=mod.calculate_weights(data)
 check_weights(w,data); causal=check_causality(mod.calculate_weights,data,full=w,checkpoints=13)
 with xr.set_options(use_bottleneck=False): rerun=mod.calculate_weights(data)
 xr.testing.assert_allclose(w,rerun,rtol=0,atol=0)
 wp=_permute(w,data); check_weights(wp,data)
 evaluator=QuantiacsEvaluator(data); base=_metrics(evaluator,w); destroyed=_metrics(evaluator,wp)
 # Regime stability is reported as the two preregistered chronological folds; no date-based strategy switch exists.
 dev4=base["development_2021_2022"]["0.04"]["sharpe_ratio"]
 dest4=destroyed["development_2021_2022"]["0.04"]["sharpe_ratio"]
 out={"schema_version":1,"candidate":"q25_volatility_contraction_breakout_v1","stage":"HARDENING_DEVELOPMENT_ONLY","data":{"min_date":str(data.time.values[0])[:10],"max_date":str(data.time.values[-1])[:10],"sha256":panel_hash(data),"holdout_2023_plus_loaded":False},"mechanics":{"bounded_prefix_replay":causal,"determinism":"PASS"},"cost_atr_percent":[4,8,12],"chronological_metrics":base,"score_identity_permutation":destroyed,"gates":{"development_4pct_positive":bool(dev4 is not None and dev4>0),"identity_permutation_weaker_on_development_4pct":bool(dev4 is not None and dest4 is not None and dev4>dest4),"holdout_unopened":True},"decision":"ADVANCE_TO_CORRELATION_AND_LIVE_ECONOMICS" if dev4 is not None and dev4>0 and dest4 is not None and dev4>dest4 else "FALSIFIED_OR_BLOCKED"}
 print(json.dumps(out,indent=2,sort_keys=True,allow_nan=False))
if __name__=="__main__": main()
