"""Frozen pre-holdout VCB/incumbent correlation and 10%-vol economics; ends 2022."""
from __future__ import annotations
import importlib, json, os
import numpy as np, xarray as xr
os.environ.setdefault("API_KEY", "default")
import qnt.data as qndata
from research.benchmark import QuantiacsEvaluator, check_weights, validate_panel
START="2015-01-01"; EVAL_START="2016-01-01"; DEV_START="2021-01-01"; END="2022-12-31"; COSTS=[0.04]
FOLDS=[{"id":"full","start":EVAL_START,"end":END},{"id":"dev","start":DEV_START,"end":END}]

def _summary(r):
    x=np.asarray(r.values,float); x=x[np.isfinite(x)]
    if x.size<2: return {"ann_return":0.0,"ann_volatility":0.0,"sharpe":None,"vol10_scale":0.0,"vol10_normalized_return":0.0}
    mean=float(np.mean(x)*365.0); vol=float(np.std(x,ddof=0)*np.sqrt(365.0)); scale=0.0 if vol<=0 else 0.10/vol
    return {"ann_return":mean,"ann_volatility":vol,"sharpe":None if vol<=0 else mean/vol,"vol10_scale":scale,"vol10_normalized_return":mean*scale}

def _corr(a,b):
    z=np.isfinite(a.values)&np.isfinite(b.values); av=np.asarray(a.values)[z]; bv=np.asarray(b.values)[z]
    return None if z.sum()<2 or np.std(av)==0 or np.std(bv)==0 else float(np.corrcoef(av,bv)[0,1])

def main():
    data=qndata.cryptodaily_load_data(min_date=START,max_date=END).sel(time=slice(START,END)); validate_panel(data,EVAL_START,END)
    if str(data.time.values[-1])[:10]>END: raise AssertionError("holdout loaded")
    vcb=importlib.import_module("strategies.generated.q25_volatility_contraction_breakout"); inc=importlib.import_module("strategies.generated.q25_deadline_hit126_consistency")
    with xr.set_options(use_bottleneck=False): vw=vcb.calculate_weights(data); iw=inc.compute_weights(data)
    check_weights(vw,data); check_weights(iw,data); e=QuantiacsEvaluator(data)
    vm,vr=e.evaluate(vw,FOLDS,COSTS); im,ir=e.evaluate(iw,FOLDS,COSTS)
    vf,if_=vr["full"].align(ir["full"],join="inner"); vd,id_=vr["dev"].align(ir["dev"],join="inner")
    full_corr=_corr(vf,if_); dev_corr=_corr(vd,id_); blend=0.5*vd+0.5*id_
    vfull=_summary(vf); vdev=_summary(vd); ifull=_summary(if_); idev=_summary(id_); bdev=_summary(blend)
    # Cross-check Sharpe against the exact Quantiacs statistic emitted by the evaluator.
    vfull["quantiacs_sharpe"]=vm["full"]["0.04"]["sharpe_ratio"]; vdev["quantiacs_sharpe"]=vm["dev"]["0.04"]["sharpe_ratio"]
    ifull["quantiacs_sharpe"]=im["full"]["0.04"]["sharpe_ratio"]; idev["quantiacs_sharpe"]=im["dev"]["0.04"]["sharpe_ratio"]
    gates={"vcb_full_2016_2022_sharpe_gt_1":bool(vfull["quantiacs_sharpe"] is not None and vfull["quantiacs_sharpe"]>1),"vcb_development_2021_2022_sharpe_gt_0":bool(vdev["quantiacs_sharpe"] is not None and vdev["quantiacs_sharpe"]>0),"absolute_development_return_correlation_lt_0_8":bool(dev_corr is not None and abs(dev_corr)<0.8),"candidate_10pct_vol_normalized_return_gt_0":bool(vdev["vol10_normalized_return"]>0),"no_holdout_loaded":True}
    out={"schema_version":1,"experiment_id":"vcb_correlation_live_20260922","data":{"max_date":str(data.time.values[-1])[:10],"holdout_2023_plus_loaded":False},"cost_atr_percent":4,"correlation":{"full_2016_2022":full_corr,"development_2021_2022":dev_corr},"candidate":{"full_2016_2022":vfull,"development_2021_2022":vdev},"incumbent":{"full_2016_2022":ifull,"development_2021_2022":idev},"equal_weight_blend":{"development_2021_2022":bdev},"gates":gates,"decision":"ADVANCE_TO_HOLDOUT_AUTHORIZATION" if all(gates.values()) else "FALSIFIED_OR_REDUNDANT"}
    print(json.dumps(out,indent=2,sort_keys=True,allow_nan=False))
if __name__=="__main__": main()
