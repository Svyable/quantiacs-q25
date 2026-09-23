import importlib.util
from pathlib import Path
import numpy as np
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def _data(seed=7, n=240, assets=("a","b","c","d","e")):
    rng=np.random.default_rng(seed); t=np.arange(np.datetime64("2020-01-01"), np.datetime64("2020-01-01")+np.timedelta64(n,"D"))
    close=100*np.exp(np.cumsum(rng.normal(.001,.025,(n,len(assets))),axis=0)); liq=np.ones_like(close)
    return xr.DataArray(np.stack([close,liq]),dims=("field","time","asset"),coords={"field":["close","is_liquid"],"time":t,"asset":assets})


def test_adapter_exactly_matches_frozen_candidate():
    frozen=_load("strategies/generated/q25_volatility_contraction_breakout.py","frozen_vcb")
    adapter=_load("submissions/q25_vcb_singlepass.py","adapter_vcb")
    d=_data(); a=frozen.calculate_weights(d); b=adapter.calculate_weights(d)
    xr.testing.assert_identical(a,b)


def test_adapter_is_deterministic_causal_and_asset_order_invariant():
    adapter=_load("submissions/q25_vcb_singlepass.py","adapter_vcb2"); d=_data(); w=adapter.calculate_weights(d)
    xr.testing.assert_identical(w,adapter.calculate_weights(d))
    cut=211; prefix=adapter.calculate_weights(d.isel(time=slice(0,cut)))
    assert float(abs(prefix-w.isel(time=slice(0,cut))).max()) <= 1e-12
    rev=d.sel(asset=list(reversed(d.asset.values))); wr=adapter.calculate_weights(rev).sel(asset=d.asset.values)
    assert float(abs(w-wr).max()) <= 1e-12


def test_adapter_respects_long_only_liquidity_name_and_gross_caps():
    adapter=_load("submissions/q25_vcb_singlepass.py","adapter_vcb3"); d=_data(); d.loc[dict(field="is_liquid",asset="a",time=d.time.values[-20:])]=0
    w=adapter.calculate_weights(d); assert float(w.min()) >= 0; assert float(w.max()) <= .25+1e-12
    assert float(w.sum("asset").max()) <= 1+1e-12
    assert float(w.sel(asset="a",time=d.time.values[-20:]).max()) == 0
