"""One-shot <=2022 screen for factor_factory_20260922; never loads 2023+ data."""
from __future__ import annotations
import importlib, json, os
import numpy as np, xarray as xr
os.environ.setdefault("API_KEY","default")
import qnt.data as qndata
from research.benchmark import QuantiacsEvaluator, check_weights, validate_panel
START="2015-01-01"; END="2022-12-31"; COSTS=[0.04,0.08,0.12]
FOLDS=[{"id":"selection","start":"2016-01-01","end":END},{"id":"research","start":"2016-01-01","end":"2020-12-31"},{"id":"development","start":"2021-01-01","end":END}]

def _summary(r):
 x=np.asarray(r.values,float); x=x[np.isfinite(x)]
 if x.size<2:return {"ann_return":0.,"ann_volatility":0.,"sharpe":None,"max_drawdown":None,"turnover":None,"vol10_normalized_return":0.}
 mean=float(x.mean()*365); vol=float(x.std(ddof=0)*np.sqrt(365)); wealth=np.cumprod(1+x); peak=np.maximum.accumulate(wealth)
 return {"ann_return":mean,"ann_volatility":vol,"sharpe":None if vol<=0 else mean/vol,"max_drawdown":float(np.min(wealth/peak-1)),"turnover":None,"vol10_normalized_return":0. if vol<=0 else mean*.10/vol}
def _corr(a,b):
 a,b=a.align(b,join="inner"); z=np.isfinite(a.values)&np.isfinite(b.values); av=np.asarray(a.values)[z]; bv=np.asarray(b.values)[z]
 return None if z.sum()<2 or np.std(av)==0 or np.std(bv)==0 else float(np.corrcoef(av,bv)[0,1])
def _sharpe(r): return _summary(r)["sharpe"]
def main():
 p=json.load(open("experiments/factor_factory_20260922/preregistration.json")); assert p["status"]=="PREREGISTERED" and p["chronology"]["holdout"][1]=="UNOPENED_FOR_THIS_EXPERIMENT"
 data=qndata.cryptodaily_load_data(min_date=START,max_date=END); assert str(data.time.values[-1])[:10]<=END; validate_panel(data,"2016-01-01",END)
 ff=importlib.import_module("strategies.generated.q25_factor_factory"); vcb=importlib.import_module("strategies.generated.q25_volatility_contraction_breakout"); inc=importlib.import_module("strategies.generated.q25_deadline_hit126_consistency")
 e=QuantiacsEvaluator(data)
 vw=vcb.calculate_weights(data); iw=inc.compute_weights(data)
 check_weights(vw,data); check_weights(iw,data); vm,vr=e.evaluate(vw,FOLDS,[.04]); im,ir=e.evaluate(iw,FOLDS,[.04])
 out={"schema_version":1,"experiment_id":p["experiment_id"],"max_date":str(data.time.values[-1])[:10],"cost_atr_percent":[4,8,12],"factors":{}}
 for name,fn in ff.FACTORS.items():
  w=fn(data)
  check_weights(w,data); m,r=e.evaluate(w,FOLDS,COSTS); dev=r["development"]; vdev=vr["development"]; idev=ir["development"]
  blend=.5*dev+.5*vdev; ssel=m["selection"]["0.04"]["sharpe_ratio"]; sdev=m["development"]["0.04"]["sharpe_ratio"]; s12=m["selection"]["0.12"]["sharpe_ratio"]
  gates={"selection_sharpe_4pct_gt_1":bool(ssel is not None and ssel>1),"development_sharpe_4pct_gt_0":bool(sdev is not None and sdev>0),"selection_sharpe_12pct_gt_0":bool(s12 is not None and s12>0),"development_abs_corr_vcb_lt_0_8":bool((_corr(dev,vdev) is not None) and abs(_corr(dev,vdev))<.8),"blend_sharpe_gt_both":bool(_sharpe(blend)>max(_sharpe(dev),_sharpe(vdev)))}
  out["factors"][name]={"metrics":m,"development_return_summary":_summary(dev),"development_vcb_correlation":_corr(dev,vdev),"development_incumbent_correlation":_corr(dev,idev),"development_50_50_vcb_blend_sharpe":_sharpe(blend),"gates":gates,"decision":"ADVANCE" if all(gates.values()) else "FALSIFIED"}
 print(json.dumps(out,indent=2,sort_keys=True,allow_nan=False))
if __name__=="__main__":main()
