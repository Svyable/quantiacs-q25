"""Mandate-V2 completed-history backfill for the frozen breadth×dispersion factor.

The candidate was selected before this procedure existed, so completed historical
windows are labelled ADAPTIVE_REUSE rather than pristine OOS evidence. The code
never fits on score-window outcomes and never crosses the 2026-10-01 live boundary.
"""
from __future__ import annotations
import importlib, json, os
from pathlib import Path
import numpy as np
import pandas as pd
os.environ.setdefault("API_KEY", "default")
import qnt.data as qndata
from research.benchmark import QuantiacsEvaluator, check_weights, validate_panel
from research.prequential import rolling_origins, exponential_recency_weights

START="2015-01-01"; IS_START="2016-01-01"; LIVE_START="2026-10-01"
MIN_TRAIN_DAYS=730; FORWARD_DAYS=90; STEP_DAYS=90; COSTS=[0.04,0.08,0.12]
HALF_LIFE_DAYS=730.0; CANDIDATE="breadth_dispersion_interaction"

def _summary(r):
    x=np.asarray(r.values,float); x=x[np.isfinite(x)]
    if x.size<2: return {"ann_return":0.0,"ann_volatility":0.0,"sharpe":None,"max_drawdown":None,"vol10_normalized_return":0.0}
    mean=float(x.mean()*365); vol=float(x.std(ddof=0)*np.sqrt(365)); wealth=np.cumprod(1+x); peak=np.maximum.accumulate(wealth)
    return {"ann_return":mean,"ann_volatility":vol,"sharpe":None if vol<=0 else mean/vol,"max_drawdown":float(np.min(wealth/peak-1)),"vol10_normalized_return":0.0 if vol<=0 else mean*.10/vol}

def _corr(a,b):
    a,b=a.align(b,join="inner"); av=np.asarray(a.values,float); bv=np.asarray(b.values,float); z=np.isfinite(av)&np.isfinite(bv)
    return None if z.sum()<2 or np.std(av[z])==0 or np.std(bv[z])==0 else float(np.corrcoef(av[z],bv[z])[0,1])

def _sharpe(r): return _summary(r)["sharpe"]

def _emit(out):
    payload=json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+"\n"
    output_path=os.environ.get("Q25_EVIDENCE_PATH")
    if output_path:
        path=Path(output_path); path.parent.mkdir(parents=True,exist_ok=True)
        tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(payload,encoding="utf-8"); tmp.replace(path)
    print(payload,end="")

def main():
    data=qndata.cryptodaily_load_data(min_date=START)
    data=data.sel(time=data.time < np.datetime64(LIVE_START))
    latest=str(data.time.values[-1])[:10]; validate_panel(data,IS_START,latest)
    ff=importlib.import_module("strategies.generated.q25_factor_factory")
    vcb=importlib.import_module("strategies.generated.q25_volatility_contraction_breakout")
    cw=ff.FACTORS[CANDIDATE](data); vw=vcb.calculate_weights(data)
    check_weights(cw,data); check_weights(vw,data)
    origins=rolling_origins(data.time.values,min_train_days=MIN_TRAIN_DAYS,forward_days=FORWARD_DAYS,step_days=STEP_DAYS,live_start=LIVE_START)
    if len(origins)<8: raise RuntimeError(f"need >=8 completed origins, got {len(origins)}")
    folds=[{"id":f"o{i:02d}","start":o.score_start.strftime("%Y-%m-%d"),"end":o.score_end.strftime("%Y-%m-%d")} for i,o in enumerate(origins)]
    full=[{"id":"current_is","start":IS_START,"end":latest}]
    e=QuantiacsEvaluator(data)
    cm,cr=e.evaluate(cw,folds,COSTS); vm,vr=e.evaluate(vw,folds,[.04])
    cfull,_=e.evaluate(cw,full,COSTS); vfull,_=e.evaluate(vw,full,[.04])
    rows=[]; ccat=[]; vcat=[]
    for i,o in enumerate(origins):
        k=f"o{i:02d}"; c=cr[k]; v=vr[k]; blend=.5*c+.5*v; ccat.append(c); vcat.append(v)
        rows.append({"window":o.as_dict(),"sharpe_4pct":cm[k]["0.04"]["sharpe_ratio"],"sharpe_8pct":cm[k]["0.08"]["sharpe_ratio"],"sharpe_12pct":cm[k]["0.12"]["sharpe_ratio"],"vcb_sharpe_4pct":vm[k]["0.04"]["sharpe_ratio"],"vcb_correlation":_corr(c,v),"blend_50_50_sharpe":_sharpe(blend)})
    # QuantiacsEvaluator returns pandas Series for 4%-ATR relative returns.
    # Keep aggregation in pandas; converting a Series via .to_pandas() is invalid.
    ca=pd.concat(ccat).sort_index(); va=pd.concat(vcat).sort_index()
    ca=ca[~ca.index.duplicated(keep="first")]; va=va[~va.index.duplicated(keep="first")]
    import xarray as xr
    car=xr.DataArray(ca.values,dims=["time"],coords={"time":ca.index}); var=xr.DataArray(va.values,dims=["time"],coords={"time":va.index})
    b=.5*car+.5*var
    ends=[pd.Timestamp(o.score_end) for o in origins]; rw=exponential_recency_weights(ends,half_life_days=HALF_LIFE_DAYS,as_of=max(ends))
    s=pd.Series([r["sharpe_4pct"] for r in rows],index=pd.DatetimeIndex(ends),dtype=float)
    recent=float((s*rw).sum())
    out={"schema_version":1,"experiment_id":"breadth_dispersion_prequential_backfill_20260923","evidence_label":"ADAPTIVE_REUSE","candidate":CANDIDATE,"latest_sponsor_date":latest,"origin_count":len(origins),"parameters":{"min_train_days":MIN_TRAIN_DAYS,"forward_days":FORWARD_DAYS,"step_days":STEP_DAYS,"recency_half_life_days":HALF_LIFE_DAYS,"cost_atr_percent":[4,8,12]},"current_is":cfull["current_is"],"current_is_vcb":vfull["current_is"],"origin_level":rows,"aggregate":{"candidate_4pct":_summary(car),"vcb_4pct":_summary(var),"candidate_vcb_correlation":_corr(car,var),"blend_50_50_4pct":_summary(b),"unweighted_mean_origin_sharpe_4pct":float(s.mean()),"recency_weighted_mean_origin_sharpe_4pct":recent,"positive_origin_fraction_4pct":float((s>0).mean())}}
    _emit(out)
if __name__=="__main__": main()
