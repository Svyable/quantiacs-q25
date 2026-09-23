"""One-shot 2023+ holdout for the preregistered breadth×dispersion candidate."""
from __future__ import annotations
import importlib, json, os
import numpy as np
os.environ.setdefault("API_KEY", "default")
import qnt.data as qndata
from research.benchmark import QuantiacsEvaluator, check_weights, validate_panel

START="2015-01-01"; HOLDOUT="2023-01-01"; COSTS=[0.04,0.08,0.12]

def _summary(r):
    x=np.asarray(r.values,float); x=x[np.isfinite(x)]
    if x.size<2:return {"ann_return":0.,"ann_volatility":0.,"sharpe":None,"max_drawdown":None,"vol10_normalized_return":0.}
    mean=float(x.mean()*365); vol=float(x.std(ddof=0)*np.sqrt(365)); wealth=np.cumprod(1+x); peak=np.maximum.accumulate(wealth)
    return {"ann_return":mean,"ann_volatility":vol,"sharpe":None if vol<=0 else mean/vol,"max_drawdown":float(np.min(wealth/peak-1)),"vol10_normalized_return":0. if vol<=0 else mean*.10/vol}

def _corr(a,b):
    a,b=a.align(b,join="inner"); z=np.isfinite(a.values)&np.isfinite(b.values); av=np.asarray(a.values)[z]; bv=np.asarray(b.values)[z]
    return None if z.sum()<2 or np.std(av)==0 or np.std(bv)==0 else float(np.corrcoef(av,bv)[0,1])

def _sharpe(r): return _summary(r)["sharpe"]

def main():
    p=json.load(open("experiments/breadth_dispersion_holdout_20260923/preregistration.json")); assert p["status"]=="PREREGISTERED" and p["holdout_start"]==HOLDOUT
    data=qndata.cryptodaily_load_data(min_date=START); end=str(data.time.values[-1])[:10]; validate_panel(data,HOLDOUT,end)
    ff=importlib.import_module("strategies.generated.q25_factor_factory"); vcb=importlib.import_module("strategies.generated.q25_volatility_contraction_breakout")
    # Use the exact frozen FACTORS registry key from the merged factor factory.
    w=ff.FACTORS["breadth_dispersion_interaction"](data); vw=vcb.calculate_weights(data); check_weights(w,data); check_weights(vw,data)
    folds=[{"id":"holdout","start":HOLDOUT,"end":end}]; e=QuantiacsEvaluator(data)
    m,r=e.evaluate(w,folds,COSTS); vm,vr=e.evaluate(vw,folds,[.04]); ret=r["holdout"]; vret=vr["holdout"]; blend=.5*ret+.5*vret
    corr=_corr(ret,vret); s4=m["holdout"]["0.04"]["sharpe_ratio"]; s12=m["holdout"]["0.12"]["sharpe_ratio"]; vs=vm["holdout"]["0.04"]["sharpe_ratio"]; bs=_sharpe(blend)
    gates={"standalone_holdout_sharpe_gt_0":bool(s4 is not None and s4>0),"standalone_holdout_12pct_cost_sharpe_gt_0":bool(s12 is not None and s12>0),"holdout_abs_return_correlation_to_vcb_lt_0_8":bool(corr is not None and abs(corr)<.8),"frozen_50_50_blend_holdout_sharpe_gt_each_component":bool(bs is not None and vs is not None and bs>max(s4,vs))}
    years={}
    for y in sorted(set(str(t)[:4] for t in ret.time.values)):
        rr=ret.sel(time=slice(f"{y}-01-01",f"{y}-12-31")); years[y]=_summary(rr)
    out={"schema_version":1,"experiment_id":p["experiment_id"],"holdout_start":HOLDOUT,"holdout_end":end,"cost_atr_percent":[4,8,12],"metrics":m["holdout"],"holdout_return_summary":_summary(ret),"vcb_holdout_sharpe_4pct":vs,"vcb_return_correlation":corr,"frozen_50_50_vcb_blend_sharpe":bs,"year_stability":years,"gates":gates,"decision":"ADVANCE" if all(gates.values()) else "FALSIFIED"}
    print(json.dumps(out,indent=2,sort_keys=True,allow_nan=False))
if __name__=="__main__":main()
