from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"strategies/generated/q25_omni_crash_consensus_sharpe7.py"
SPEC=importlib.util.spec_from_file_location("omni_crash_consensus_test",PATH)
assert SPEC and SPEC.loader
S=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(S)

from submissions import q25_sharpe7_vol2_multipass as FROZEN


def _panel(days:int,assets:int,seed:int,stock:bool=False)->xr.DataArray:
    rng=np.random.default_rng(seed)
    idx=pd.date_range("2018-01-01",periods=days,freq="D")
    ret=rng.normal(0.00015 if stock else 0.0004,0.012 if stock else 0.03,(days,assets))
    close=100.0*np.exp(np.cumsum(ret,axis=0))
    op=close*np.exp(rng.normal(0.0,0.002,(days,assets)))
    high=np.maximum(op,close)*(1.0+np.abs(rng.normal(0.0,0.004,(days,assets))))
    low=np.minimum(op,close)*(1.0-np.abs(rng.normal(0.0,0.004,(days,assets))))
    vol=np.exp(rng.normal(10.0,1.0,(days,assets)))
    liq=np.ones((days,assets))
    values=np.stack([op,high,low,close,vol,liq],axis=0)
    return xr.DataArray(
        values,dims=("field","time","asset"),
        coords={
            "field":["open","high","low","close","vol","is_liquid"],
            "time":idx,
            "asset":[f"A{i:03d}" for i in range(assets)],
        },
        name="stock" if stock else "cryptodaily",
    )


def _data(days:int=1100):
    return {
        "crypto":_panel(days,10,211,False),
        "spx":_panel(days,35,223,True),
        "ndx":_panel(days,32,227,True),
    }


def test_carrier_matches_promoted_sharpe7_exactly():
    data=_data(500)
    got=S._sharpe7_carrier(data["crypto"])
    expected=FROZEN.strategy(data["crypto"],{"window":7},"base")
    np.testing.assert_allclose(got.values,expected.values,atol=0.0,rtol=0.0)


def test_modes_respect_constraints():
    data=_data()
    modes=(
        "base","always_static","stock_majority","stock_unanimous",
        "crypto_only","cross_unanimous","inverted_cross","cross_majority",
    )
    for mode in modes:
        w=S.calculate_weights(data,mode)
        assert np.isfinite(w.values).all()
        assert float(w.min())>=-1e-12
        assert float(w.max())<=0.25+1e-12
        assert float(w.sum("asset").max())<=1.0+1e-12


def test_cross_majority_prefix_causal():
    data=_data()
    full=S.calculate_weights(data,"cross_majority")
    for cut in (800,950,1099):
        prefix={k:v.isel(time=slice(0,cut+1)) for k,v in data.items()}
        got=S.calculate_weights(prefix,"cross_majority")
        np.testing.assert_allclose(
            got.values,
            full.isel(time=slice(0,cut+1)).values,
            atol=1e-12,rtol=0.0,
        )


def test_stock_threshold_is_robust_median_center():
    idx=pd.date_range("2025-01-01",periods=5,freq="D")
    experts=pd.DataFrame(
        {
            "a":[0.6,0.6,0.4,0.6,np.nan],
            "b":[0.6,0.4,0.4,0.6,np.nan],
            "c":[0.6,0.6,0.4,0.4,np.nan],
            "d":[0.4,0.6,0.4,0.6,np.nan],
        },index=idx
    )
    frag=pd.DataFrame({"fragile":[True]*5},index=idx)
    act=S._activation(experts,frag,"cross_majority")
    assert act.iloc[0]>0
    assert act.iloc[1]>0
    assert act.iloc[2]==0
    assert act.iloc[3]>0
    assert act.iloc[4]==0


def test_crypto_confirmation_changes_stock_majority_policy():
    data=_data()
    a=S.calculate_weights(data,"stock_majority").values
    b=S.calculate_weights(data,"cross_majority").values
    assert np.max(np.abs(a-b))>1e-8


def test_inverted_control_is_distinct():
    data=_data()
    a=S.calculate_weights(data,"cross_majority").values
    b=S.calculate_weights(data,"inverted_cross").values
    assert np.max(np.abs(a-b))>1e-8
