from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

PATH = Path("strategies/generated/omni_cross_asset_wave2_r1.py")
spec = importlib.util.spec_from_file_location("omni_wave2_r1", PATH)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _panel(seed: int, periods: int = 950, assets: int = 30) -> xr.DataArray:
    rng=np.random.default_rng(seed)
    dates=pd.bdate_range("2013-01-02", periods=periods)
    common=rng.normal(0.0002,0.009,size=(periods,1))
    noise=rng.normal(0.0,0.013,size=(periods,assets))
    ret=0.60*common+0.40*noise
    close=100*np.exp(np.cumsum(ret,axis=0))
    liquid=np.ones_like(close)
    return xr.DataArray(np.stack([close,liquid]),dims=("field","time","asset"),coords={"field":["close","is_liquid"],"time":dates,"asset":[f"S{i:03d}" for i in range(assets)]})


def test_single_panel_wave2_states_are_bounded_and_causal():
    stocks=_panel(12)
    end=pd.Timestamp(stocks.time.values[875])
    full_ctx=mod.BASE.FRONTIER._stock_context(stocks)
    cut_ctx=mod.BASE.FRONTIER._stock_context(stocks.sel(time=slice(None,end)))
    for fn in (mod._correlation_acceleration,mod._vol_surface_curvature):
        full=fn(full_ctx)
        cut=fn(cut_ctx)
        for key in ("primary","ablation","inverted"):
            assert cut[key].dropna().between(0.0,1.0).all()
            assert np.isclose(float(full[key].loc[end]),float(cut[key].loc[end]),atol=1e-12,rtol=0.0,equal_nan=True)


def test_dual_panel_disagreement_is_bounded_and_causal():
    spx=_panel(21)
    ndx=_panel(22)
    end=pd.Timestamp(spx.time.values[875])
    full=mod._panel_disagreement(spx,ndx)
    cut=mod._panel_disagreement(spx.sel(time=slice(None,end)),ndx.sel(time=slice(None,end)))
    for key in ("primary","ablation","inverted"):
        assert cut[key].dropna().between(0.0,1.0).all()
        assert np.isclose(float(full[key].loc[end]),float(cut[key].loc[end]),atol=1e-12,rtol=0.0,equal_nan=True)
