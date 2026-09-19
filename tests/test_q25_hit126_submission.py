"""Submission artifact must reproduce the measured hit126 implementation exactly."""
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
from strategies.generated import q25_deadline_hit126_consistency as measured

def panel(n=520, assets=8):
    rng=np.random.default_rng(2026091803)
    dates=pd.date_range("2015-01-01",periods=n,freq="D")
    drift=np.linspace(-0.0004,0.0015,assets)
    ret=rng.normal(0,0.018,(n,assets))+drift[None,:]
    close=100*np.exp(np.cumsum(ret,axis=0))
    opened=np.vstack([close[:1],close[:-1]])
    high=np.maximum(opened,close)*1.012
    low=np.minimum(opened,close)*0.988
    vol=rng.lognormal(10,.5,(n,assets))
    liquid=np.ones((n,assets)); liquid[350:370,-1]=0
    return xr.DataArray(
        np.stack([opened,high,low,close,vol,liquid]),
        dims=("field","time","asset"),
        coords={"field":["open","high","low","close","vol","is_liquid"],
                "time":dates,"asset":[f"A{i}" for i in range(assets)]},
        name="cryptodaily",
    )

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"submissions"/"q25_hit126_consistency_singlepass.py"

def _load_submission():
    spec=importlib.util.spec_from_file_location("q25_hit126_submission",PATH)
    assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_submission_matches_measured_source_weights():
    data=panel()
    submission=_load_submission()
    expected=measured.compute_weights(data)
    got=submission.compute_weights(data)
    xr.testing.assert_allclose(expected,got)
    assert submission.HIT_WINDOW==measured.HIT_WINDOW
    assert submission.TOP_K==measured.TOP_K
    assert submission.NAME_CAP==measured.NAME_CAP
