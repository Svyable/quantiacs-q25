"""Synthetic mechanics for frontier_20260911g; no market-performance evidence."""
from pathlib import Path
import hashlib, json
import numpy as np, pandas as pd, pytest, xarray as xr
from research.benchmark import ROOT, check_causality, check_weights, load_module
from research.iteration import load_manifest

CAMPAIGN="frontier_20260911g"
FAMILIES=("topology_rank_stability","topology_reconnection","response_sign_asymmetry")

def panel(n=520,assets=8):
    rng=np.random.default_rng(20260911)
    common=rng.normal(.0003,.011,(n,1)); shocks=rng.normal(0,.022,(n,assets))
    close=100*np.exp(np.cumsum(common+shocks,axis=0))
    opened=np.vstack([close[:1],close[:-1]])*np.exp(rng.normal(0,.004,(n,assets)))
    high=np.maximum(close,opened)*(1+rng.uniform(.003,.03,(n,assets)))
    low=np.minimum(close,opened)*(1-rng.uniform(.003,.03,(n,assets)))
    vol=rng.lognormal(10,.7,(n,assets)); liquid=np.ones((n,assets),float)
    liquid[:35,-1]=0; liquid[100:130,-1]=0; liquid[210:250,-2]=0; liquid[390:395,:]=0
    return xr.DataArray(np.stack([opened,high,low,close,vol,liquid]),
        dims=("field","time","asset"),
        coords={"field":["open","high","low","close","vol","is_liquid"],
                 "time":pd.date_range("2015-01-01",periods=n),
                 "asset":[f"A{i}" for i in range(assets)]},name="cryptodaily")

def module(f):
    return load_module(ROOT/f"strategies/generated/{CAMPAIGN}_{f}.py")

@pytest.mark.parametrize("family",FAMILIES)
@pytest.mark.parametrize("mode",("base","ablation","falsifier"))
def test_causal_admissible_order_invariant(family,mode):
    d=panel(); m=module(family); fn=lambda x:m.strategy(x,mode=mode)
    w=fn(d); assert check_causality(fn,d,w)["status"]=="PASS"; check_weights(w,d)
    assert np.count_nonzero(w.values)>0
    shuffled=d.sel(asset=list(reversed(d.asset.values)))
    xr.testing.assert_allclose(fn(shuffled).sel(asset=d.asset),w)

@pytest.mark.parametrize("family",FAMILIES)
def test_controls_change_book(family):
    d=panel(); m=module(family)
    b=m.strategy(d,mode="base"); a=m.strategy(d,mode="ablation"); f=m.strategy(d,mode="falsifier")
    assert float(abs(b-a).sum())>0
    assert float(abs(b-f).sum())>0

def test_registration_contract():
    directory=ROOT/"experiments"/CAMPAIGN
    slate=json.loads((directory/"idea_slate.json").read_text())
    assert len(slate)==24 and all(x["performance_seen_before_score"] is False for x in slate)
    preregs=list(directory.glob("*/preregistration.json")); assert len(preregs)==3
    for p in preregs:
        assert hashlib.sha256(p.read_bytes()).hexdigest()==p.with_suffix(".sha256").read_text().strip()
    manifest=load_manifest(directory/"manifest.json")
    assert len(manifest["candidates"])==15
    assert {x["family"] for x in manifest["candidates"]}==set(FAMILIES)
    assert manifest["automatic_promotion"] is False
