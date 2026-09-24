"""Evaluate the preregistered 2%-band VCB x breadth ensemble without retuning."""
from __future__ import annotations
import importlib, json, os
from pathlib import Path
import numpy as np
import pandas as pd
os.environ.setdefault("API_KEY","default")
import qnt.data as qndata
from research.benchmark import QuantiacsEvaluator, check_weights, validate_panel
from research.prequential import rolling_origins, exponential_recency_weights

START="2015-01-01"; IS_START="2016-01-01"; LIVE_START="2026-10-01"; COSTS=[.04,.08,.12]

def summary(r):
    x=np.asarray(r.values,float); x=x[np.isfinite(x)]
    mean=float(x.mean()*365); vol=float(x.std(ddof=0)*np.sqrt(365)); wealth=np.cumprod(1+x); peak=np.maximum.accumulate(wealth)
    return {"ann_return":mean,"ann_volatility":vol,"sharpe":None if vol<=0 else mean/vol,"max_drawdown":float(np.min(wealth/peak-1)),"vol10_normalized_return":0 if vol<=0 else mean*.1/vol}

def corr(a,b):
    a,b=a.align(b,join="inner"); z=np.isfinite(a.values)&np.isfinite(b.values)
    return None if z.sum()<2 else float(np.corrcoef(a.values[z],b.values[z])[0,1])

def turnover(w):
    x=np.asarray(w.transpose("time","asset").fillna(0).values,float)
    return float(np.abs(np.diff(x,axis=0)).sum(axis=1).mean())

def emit(out):
    payload=json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+"\n"; p=os.environ.get("Q25_EVIDENCE_PATH")
    if p:
        path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(payload); tmp.replace(path)
    print(payload,end="")

def main():
    data=qndata.cryptodaily_load_data(min_date=START); data=data.sel(time=data.time < np.datetime64(LIVE_START)); latest=str(data.time.values[-1])[:10]; validate_panel(data,IS_START,latest)
    ff=importlib.import_module("strategies.generated.q25_factor_factory"); vcb=importlib.import_module("strategies.generated.q25_volatility_contraction_breakout"); ens=importlib.import_module("strategies.generated.q25_vcb_breadth_turnover_ensemble")
    bw=ff.FACTORS["breadth_dispersion_interaction"](data); vw=vcb.calculate_weights(data); static=.5*bw+.5*vw
    liquid=data.sel(field="is_liquid").fillna(0)>0
    band=ens.apply_no_trade_band(static,eligible=liquid)
    lag=ens.apply_no_trade_band(static.shift(time=1).fillna(0),eligible=liquid)
    for w in (bw,vw,static,band,lag): check_weights(w,data)
    origins=rolling_origins(data.time.values,min_train_days=730,forward_days=90,step_days=90,live_start=LIVE_START); folds=[{"id":f"o{i:02d}","start":o.score_start.strftime("%Y-%m-%d"),"end":o.score_end.strftime("%Y-%m-%d")} for i,o in enumerate(origins)]; full=[{"id":"current_is","start":IS_START,"end":latest}]
    e=QuantiacsEvaluator(data); bm,br=e.evaluate(band,folds,COSTS); sm,sr=e.evaluate(static,folds,[.04]); lm,lr=e.evaluate(lag,folds,[.04]); cm,cr=e.evaluate(bw,folds,[.04]); vm,vr=e.evaluate(vw,folds,[.04]); bf,_=e.evaluate(band,full,COSTS); sf,_=e.evaluate(static,full,[.04])
    rows=[]; bcat=[]; scat=[]; ccat=[]; vcat=[]; lcat=[]
    for i,o in enumerate(origins):
        k=f"o{i:02d}"; bcat.append(br[k]); scat.append(sr[k]); ccat.append(cr[k]); vcat.append(vr[k]); lcat.append(lr[k]); rows.append({"window":o.as_dict(),"band_sharpe_4pct":bm[k]["0.04"]["sharpe_ratio"],"static_sharpe_4pct":sm[k]["0.04"]["sharpe_ratio"],"lag_control_sharpe_4pct":lm[k]["0.04"]["sharpe_ratio"]})
    def cat(xs):
        x=pd.concat(xs).sort_index(); return x[~x.index.duplicated(keep="first")]
    b,s,c,v,l=map(cat,(bcat,scat,ccat,vcat,lcat)); b,s=b.align(s,join="inner"); b,c=b.align(c,join="inner"); b,v=b.align(v,join="inner"); b,l=b.align(l,join="inner")
    ends=[pd.Timestamp(o.score_end) for o in origins]; rw=exponential_recency_weights(ends,half_life_days=730,as_of=max(ends)); osh=pd.Series([r["band_sharpe_4pct"] for r in rows],index=pd.DatetimeIndex(ends),dtype=float)
    tstatic=turnover(static.sel(time=slice(IS_START,latest))); tband=turnover(band.sel(time=slice(IS_START,latest)))
    out={"schema_version":1,"experiment_id":"vcb_breadth_turnover_ensemble_20260924","evidence_label":"ADAPTIVE_REUSE","latest_sponsor_date":latest,"origin_count":len(origins),"parameters":{"band":.02,"cost_atr_percent":[4,8,12]},"current_is":{"band":bf["current_is"],"static":sf["current_is"],"static_turnover":tstatic,"band_turnover":tband,"turnover_reduction":1-tband/tstatic},"aggregate":{"band_4pct":summary(b),"static_4pct":summary(s),"lag_control_4pct":summary(l),"correlation_breadth":corr(b,c),"correlation_vcb":corr(b,v),"positive_origin_fraction":float((osh>0).mean()),"mean_origin_sharpe":float(osh.mean()),"recency_weighted_origin_sharpe":float((osh*rw).sum())},"origin_level":rows}
    emit(out)
if __name__=="__main__": main()
