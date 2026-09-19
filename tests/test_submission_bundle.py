"""Integrity checks for the deadline submission bundle."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT=Path(__file__).resolve().parents[1]


def _load(path: Path, name: str):
    spec=importlib.util.spec_from_file_location(name,path)
    assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _panel(n=520, assets=8):
    rng=np.random.default_rng(2026091803)
    dates=pd.date_range("2015-01-01",periods=n,freq="D")
    drift=np.linspace(-0.0004,0.0015,assets)
    ret=rng.normal(0,0.018,(n,assets))+drift[None,:]
    close=100*np.exp(np.cumsum(ret,axis=0))
    opened=np.vstack([close[:1],close[:-1]])
    high=np.maximum(opened,close)*1.012
    low=np.minimum(opened,close)*0.988
    vol=rng.lognormal(10,.5,(n,assets))
    liquid=np.ones((n,assets))
    liquid[350:370,-1]=0
    return xr.DataArray(
        np.stack([opened,high,low,close,vol,liquid]),
        dims=("field","time","asset"),
        coords={
            "field":["open","high","low","close","vol","is_liquid"],
            "time":dates,
            "asset":[f"A{i}" for i in range(assets)],
        },
        name="cryptodaily",
    )


def test_sota_submission_is_exact_frozen_source_copy():
    assert (
        ROOT/"submissions/q25_sota_meta_ensemble_multipass.py"
    ).read_text() == (
        ROOT/"strategies/q25_sota_meta_ensemble.py"
    ).read_text()


def test_lattice_submission_is_exact_frozen_source_copy():
    assert (
        ROOT/"submissions/q25_lattice_consensus_multipass.py"
    ).read_text() == (
        ROOT/"strategies/generated/ebenezar_20260912_lattice_consensus.py"
    ).read_text()


def test_hit126_submission_constraints_and_order_invariance():
    path=ROOT/"submissions/q25_hit126_consistency_singlepass.py"
    m=_load(path,"q25_hit126_submission")
    data=_panel()
    w=m.compute_weights(data)
    assert w.dims==("time","asset")
    assert float(w.min())>=-1e-12
    assert float(w.max())<=m.NAME_CAP+1e-12
    assert float(w.sum("asset").max())<=1.0+1e-12
    liquid=data.sel(field="is_liquid").transpose("time","asset")
    assert float(w.where(liquid<=0,0).sum())==0.0
    rev=data.sel(asset=list(reversed(data.asset.values)))
    xr.testing.assert_allclose(w,m.compute_weights(rev).sel(asset=data.asset))


def test_hit126_prefix_causality():
    path=ROOT/"submissions/q25_hit126_consistency_singlepass.py"
    m=_load(path,"q25_hit126_submission_prefix")
    data=_panel()
    full=m.compute_weights(data)
    for cut in (250,350,430,510):
        latest=m.strategy(data.isel(time=slice(0,cut+1)))
        xr.testing.assert_allclose(latest,full.isel(time=cut,drop=True))
