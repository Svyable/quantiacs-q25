"""Frozen pre-holdout VCB/incumbent correlation and 10%-vol economics; ends 2022."""
from __future__ import annotations
import importlib, json, os
import numpy as np, xarray as xr
os.environ.setdefault("API_KEY", "default")
import qnt.data as qndata
from research.benchmark import QuantiacsEvaluator, check_weights, validate_panel
START="2015-01-01"; EVAL_START="2016-01-01"; DEV_START="2021-01-01"; END="2022-12-31"; COST=0.04

def _returns(evaluator, weights):
    # Use the repository evaluator's official 4% ATR cost path, then retain its daily net returns.
    return evaluator.daily_returns(weights, slippage_factor=COST).sel(time=slice(EVAL_START, END)).fillna(0.0)

def _summary(r):
    x=np.asarray(r.values, float); x=x[np.isfinite(x)]
    if x.size < 2: return {"ann_return":0.0,"ann_volatility":0.0,"sharpe":None,"vol10_scale":0.0,"vol10_normalized_return":0.0}
    mean=float(np.mean(x)*365.0); vol=float(np.std(x, ddof=0)*np.sqrt(365.0)); scale=0.0 if vol<=0 else 0.10/vol
    return {"ann_return":mean,"ann_volatility":vol,"sharpe":None if vol<=0 else mean/vol,"vol10_scale":scale,"vol10_normalized_return":mean*scale}

def _corr(a,b,start):
    aa=a.sel(time=slice(start,END)); bb=b.sel(time=slice(start,END)); aa,bb=xr.align(aa,bb,join="inner")
    av=np.asarray(aa.values,float); bv=np.asarray(bb.values,float); ok=np.isfinite(av)&np.isfinite(bv)
    return None if ok.sum()<2 or np.std(av[ok])==0 or np.std(bv[ok])==0 else float(np.corrcoef(av[ok],bv[ok])[0,1])

def main():
    data=qndata.cryptodaily_load_data(min_date=START,max_date=END).sel(time=slice(START,END)); validate_panel(data,EVAL_START,END)
    if str(data.time.values[-1])[:10] > END: raise AssertionError("holdout loaded")
    vcb=importlib.import_module("strategies.generated.q25_volatility_contraction_breakout")
    inc=importlib.import_module("strategies.generated.q25_deadline_hit126_consistency")
    with xr.set_options(use_bottleneck=False): vw=vcb.calculate_weights(data); iw=inc.compute_weights(data)
    check_weights(vw,data); check_weights(iw,data); e=QuantiacsEvaluator(data)
    vr=_returns(e,vw); ir=_returns(e,iw); vr,ir=xr.align(vr,ir,join="inner"); blend=0.5*vr+0.5*ir
    full_corr=_corr(vr,ir,EVAL_START); dev_corr=_corr(vr,ir,DEV_START)
    vfull=_summary(vr); vdev=_summary(vr.sel(time=slice(DEV_START,END))); ifull=_summary(ir); idev=_summary(ir.sel(time=slice(DEV_START,END))); bdev=_summary(blend.sel(time=slice(DEV_START,END)))
    gates={"vcb_full_2016_2022_sharpe_gt_1":bool(vfull["sharpe"] is not None and vfull["sharpe"]>1),"vcb_development_2021_2022_sharpe_gt_0":bool(vdev["sharpe"] is not None and vdev["sharpe"]>0),"absolute_development_return_correlation_lt_0_8":bool(dev_corr is not None and abs(dev_corr)<0.8),"candidate_10pct_vol_normalized_return_gt_0":bool(vdev["vol10_normalized_return"]>0),"no_holdout_loaded":True}
    out={"schema_version":1,"experiment_id":"vcb_correlation_live_20260922","data":{"max_date":str(data.time.values[-1])[:10],"holdout_2023_plus_loaded":False},"cost_atr_percent":4,"correlation":{"full_2016_2022":full_corr,"development_2021_2022":dev_corr},"candidate":{"full_2016_2022":vfull,"development_2021_2022":vdev},"incumbent":{"full_2016_2022":ifull,"development_2021_2022":idev},"equal_weight_blend":{"development_2021_2022":bdev},"gates":gates,"decision":"ADVANCE_TO_HOLDOUT_AUTHORIZATION" if all(gates.values()) else "FALSIFIED_OR_REDUNDANT"}
    print(json.dumps(out,indent=2,sort_keys=True,allow_nan=False))
if __name__=="__main__": main()
