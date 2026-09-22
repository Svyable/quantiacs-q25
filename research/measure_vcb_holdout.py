"""One-shot frozen VCB/incumbent/blend holdout evaluation authorized by vcb_holdout_20260922."""
from __future__ import annotations
import importlib, json, os
import numpy as np, xarray as xr
os.environ.setdefault("API_KEY", "default")
import qnt.data as qndata
from research.benchmark import QuantiacsEvaluator, check_weights, validate_panel
START="2015-01-01"; EVAL_START="2016-01-01"; HOLDOUT_START="2023-01-01"; COSTS=[0.04]

def _summary(r):
    x=np.asarray(r.values,float); x=x[np.isfinite(x)]
    if x.size<2: return {"ann_return":0.0,"ann_volatility":0.0,"sharpe":None,"max_drawdown":None,"turnover":None,"vol10_normalized_return":0.0}
    mean=float(np.mean(x)*365.0); vol=float(np.std(x,ddof=0)*np.sqrt(365.0)); scale=0.0 if vol<=0 else 0.10/vol
    wealth=np.cumprod(1.0+x); peak=np.maximum.accumulate(wealth); mdd=float(np.min(wealth/peak-1.0))
    return {"ann_return":mean,"ann_volatility":vol,"sharpe":None if vol<=0 else mean/vol,"max_drawdown":mdd,"vol10_normalized_return":mean*scale}

def _corr(a,b):
    a,b=a.align(b,join="inner"); z=np.isfinite(a.values)&np.isfinite(b.values); av=np.asarray(a.values)[z]; bv=np.asarray(b.values)[z]
    return None if z.sum()<2 or np.std(av)==0 or np.std(bv)==0 else float(np.corrcoef(av,bv)[0,1])

def main():
    p=json.load(open("experiments/vcb_holdout_20260922/preregistration.json")); assert p["status"]=="PREREGISTERED_HOLDOUT_UNOPENED" and p["evaluation"]["one_shot"] and p["cost_atr_percent"]==4
    data=qndata.cryptodaily_load_data(min_date=START); end=str(data.time.values[-1])[:10]; validate_panel(data,EVAL_START,end)
    assert end>=HOLDOUT_START
    folds=[{"id":"full","start":EVAL_START,"end":end},{"id":"holdout","start":HOLDOUT_START,"end":end}]
    vcb=importlib.import_module("strategies.generated.q25_volatility_contraction_breakout"); inc=importlib.import_module("strategies.generated.q25_deadline_hit126_consistency")
    with xr.set_options(use_bottleneck=False): vw=vcb.calculate_weights(data); iw=inc.compute_weights(data)
    check_weights(vw,data); check_weights(iw,data); e=QuantiacsEvaluator(data)
    vm,vr=e.evaluate(vw,folds,COSTS); im,ir=e.evaluate(iw,folds,COSTS)
    vf,if_=vr["full"].align(ir["full"],join="inner"); vh,ih=vr["holdout"].align(ir["holdout"],join="inner"); bh=0.5*vh+0.5*ih
    vfull=_summary(vf); vh_s=_summary(vh); ih_s=_summary(ih); bh_s=_summary(bh)
    vfull["quantiacs_sharpe"]=vm["full"]["0.04"]["sharpe_ratio"]; vh_s["quantiacs_sharpe"]=vm["holdout"]["0.04"]["sharpe_ratio"]; ih_s["quantiacs_sharpe"]=im["holdout"]["0.04"]["sharpe_ratio"]
    # Blend is preselected; report return-stream Sharpe under the same exact-cost component streams.
    bh_s["quantiacs_sharpe"]=bh_s["sharpe"]
    gates={"candidate_holdout_sharpe_gt_0":bool(vh_s["quantiacs_sharpe"] is not None and vh_s["quantiacs_sharpe"]>0),"candidate_holdout_vol10_normalized_return_gt_0":bool(vh_s["vol10_normalized_return"]>0),"candidate_full_2016_latest_sharpe_gt_1":bool(vfull["quantiacs_sharpe"] is not None and vfull["quantiacs_sharpe"]>1),"no_holdout_retuning":True}
    out={"schema_version":1,"experiment_id":"vcb_holdout_20260922","data":{"start":HOLDOUT_START,"max_date":end},"cost_atr_percent":4,"candidate":{"full_2016_latest":vfull,"holdout_2023_latest":vh_s},"incumbent":{"holdout_2023_latest":ih_s},"equal_weight_blend":{"holdout_2023_latest":bh_s},"candidate_incumbent_return_correlation":_corr(vh,ih),"gates":gates,"decision":"ADVANCE" if all(gates.values()) else "HOLDOUT_FALSIFIED"}
    print(json.dumps(out,indent=2,sort_keys=True,allow_nan=False))
if __name__=="__main__": main()
