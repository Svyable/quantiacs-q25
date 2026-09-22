import importlib.util
from pathlib import Path
import numpy as np
import xarray as xr
ROOT=Path(__file__).resolve().parents[1]
FILES=["q25_residual_momentum.py","q25_breadth_conditioned_trend.py","q25_liquidity_persistence.py"]

def load(name):
    p=ROOT/"strategies"/"generated"/name
    s=importlib.util.spec_from_file_location(name[:-3],p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def fixture(seed=41,days=190,assets=10):
    rng=np.random.default_rng(seed); t=np.arange(np.datetime64("2024-01-01"),np.datetime64("2024-01-01")+days)
    a=np.array([f"A{i}" for i in range(assets)]); r=rng.normal(0.0007,0.025,(days,assets))
    close=100*np.exp(np.cumsum(r,axis=0)); liquid=np.ones_like(close); liquid[-15:,2]=0
    return xr.DataArray(np.stack([close,liquid]),dims=("field","time","asset"),coords={"field":["close","is_liquid"],"time":t,"asset":a})
def test_new_alpha_families_mechanics_order_and_causality():
    d=fixture()
    for name in FILES:
        m=load(name); w=m.calculate_weights(d)
        assert float(w.min())>=-1e-15
        assert float(w.max())<=0.25+1e-12
        assert float(w.sum("asset").max())<=1.0+1e-12
        assert float(abs(w.sel(asset="A2",time=d.time[-15:])).max())==0.0
        wr=m.calculate_weights(d.sel(asset=d.asset.values[::-1])).sel(asset=d.asset.values)
        xr.testing.assert_allclose(w,wr,rtol=0,atol=1e-12)
        cut=160
        xr.testing.assert_allclose(w.isel(time=slice(0,cut)),m.calculate_weights(d.isel(time=slice(0,cut))),rtol=0,atol=1e-12)
def test_new_families_are_not_identical_on_fixture():
    d=fixture()
    ws=[load(n).calculate_weights(d).values for n in FILES]
    assert not np.allclose(ws[0],ws[1])
    assert not np.allclose(ws[0],ws[2])
    assert not np.allclose(ws[1],ws[2])
