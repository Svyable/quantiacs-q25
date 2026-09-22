import importlib.util
from pathlib import Path
import numpy as np, xarray as xr
ROOT=Path(__file__).resolve().parents[1]
FILES=["q25_volatility_contraction_breakout.py","q25_drawdown_recovery.py","q25_cross_sectional_dispersion.py","q25_trend_consistency.py"]
def load(n):
 s=importlib.util.spec_from_file_location(n[:-3],ROOT/"strategies"/"generated"/n); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def fixture(seed=92,days=200,assets=10):
 rng=np.random.default_rng(seed); t=np.arange(np.datetime64("2024-01-01"),np.datetime64("2024-01-01")+days); a=np.array([f"A{i}" for i in range(assets)])
 rr=rng.normal(.0008,.025,(days,assets)); rr[80:120,0]+=.003; rr[120:150,1]-=.002; close=100*np.exp(np.cumsum(rr,axis=0)); liq=np.ones_like(close); liq[-12:,3]=0
 return xr.DataArray(np.stack([close,liq]),dims=("field","time","asset"),coords={"field":["close","is_liquid"],"time":t,"asset":a})
def test_pack2_mechanics_order_prefix():
 d=fixture()
 for n in FILES:
  m=load(n); w=m.calculate_weights(d)
  assert float(w.min())>=-1e-15 and float(w.max())<=.25+1e-12 and float(w.sum("asset").max())<=1+1e-12
  assert float(abs(w.sel(asset="A3",time=d.time[-12:])).max())==0
  xr.testing.assert_allclose(w,m.calculate_weights(d.sel(asset=d.asset.values[::-1])).sel(asset=d.asset.values),rtol=0,atol=1e-12)
  cut=165; xr.testing.assert_allclose(w.isel(time=slice(0,cut)),m.calculate_weights(d.isel(time=slice(0,cut))),rtol=0,atol=1e-12)
