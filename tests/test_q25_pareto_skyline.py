from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np, pandas as pd, xarray as xr

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"strategies/generated/q25_pareto_skyline.py"
SPEC=importlib.util.spec_from_file_location("q25_pareto_skyline_test",PATH)
assert SPEC and SPEC.loader
S=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(S)
from submissions import q25_sharpe7_vol2_multipass as FROZEN

def _panel(days=900,assets=10,seed=23):
    rng=np.random.default_rng(seed); idx=pd.date_range("2018-01-01",periods=days,freq="D")
    ret=rng.normal(0.0005,0.03,(days,assets)); close=100*np.exp(np.cumsum(ret,axis=0))
    op=close*np.exp(rng.normal(0,0.003,(days,assets)))
    high=np.maximum(op,close)*(1+np.abs(rng.normal(0,0.006,(days,assets))))
    low=np.minimum(op,close)*(1-np.abs(rng.normal(0,0.006,(days,assets))))
    vol=np.exp(rng.normal(10,1,(days,assets))); liq=np.ones((days,assets))
    return xr.DataArray(np.stack([op,high,low,close,vol,liq]),dims=("field","time","asset"),
        coords={"field":["open","high","low","close","vol","is_liquid"],"time":idx,"asset":[f"A{i:03d}" for i in range(assets)]})

def test_base_matches_sharpe7():
    d=_panel(); a=S.calculate_weights(d,"base_sharpe7"); b=FROZEN.strategy(d,{"window":7},"base")
    np.testing.assert_allclose(a.values,b.values,atol=0,rtol=0)

def test_modes_are_admissible_and_distinct():
    d=_panel(); modes=("no_pareto","frontier_only","pareto_le2","dominated_tail","pareto_le1")
    out={}
    for m in modes:
        w=S.calculate_weights(d,m); out[m]=w.values
        assert np.isfinite(w.values).all(); assert float(w.min())>=-1e-12
        assert float(w.max())<=S.NAME_CAP+1e-12; assert float(w.sum("asset").max())<=1+1e-12
    assert np.max(np.abs(out["pareto_le1"]-out["no_pareto"]))>1e-8
    assert np.max(np.abs(out["pareto_le1"]-out["dominated_tail"]))>1e-8

def test_prefix_causal():
    d=_panel(); full=S.calculate_weights(d,"pareto_le1")
    for cut in (300,600,899):
        got=S.calculate_weights(d.isel(time=slice(0,cut+1)),"pareto_le1")
        np.testing.assert_allclose(got.values,full.isel(time=slice(0,cut+1)).values,atol=1e-12,rtol=0)

def test_asset_order_invariant():
    d=_panel(); base=S.calculate_weights(d,"pareto_le1")
    rev=S.calculate_weights(d.sel(asset=list(reversed(d.asset.values))),"pareto_le1").sel(asset=d.asset.values)
    np.testing.assert_allclose(rev.values,base.values,atol=1e-12,rtol=0)

def test_dominance_count_direction():
    idx=pd.date_range("2025-01-01",periods=1); assets=["A","B","C"]
    def da(v): return xr.DataArray([v],dims=("time","asset"),coords={"time":idx,"asset":assets})
    liq=da([1,1,1]); s=da([3,2,1]); vol=da([1,2,3]); trend=da([3,2,1]); mom=da([3,2,1]); dd=da([0,-.1,-.2])
    counts,valid=S._dominance_count(liq,s,vol,trend,mom,dd)
    np.testing.assert_allclose(counts.values,[[0,1,2]])
    np.testing.assert_allclose(valid.values,[[1,1,1]])


def test_bounded_replay_matches_full_history_exactly():
    d = _panel(days=1400, assets=10, seed=47)
    full = S.calculate_weights(d, "pareto_le1")
    for cut in (500, 800, 1100, 1399):
        dt = d.time.values[cut]
        tail = d.sel(time=slice(dt - np.timedelta64(S.LOOKBACK_DAYS, "D"), dt))
        got = S.calculate_weights(tail, "pareto_le1").sel(time=dt)
        expected = full.sel(time=dt)
        np.testing.assert_allclose(got.values, expected.values, atol=0.0, rtol=0.0)


def test_local_rolling_arithmetic_is_prefix_length_invariant():
    d = _panel(days=1400, assets=10, seed=53)
    close, _ = S._close_liquid(d)
    ret = S._returns(close)
    dt = d.time.values[-1]
    tail = d.sel(time=slice(dt - np.timedelta64(S.LOOKBACK_DAYS, "D"), dt))
    tail_close, _ = S._close_liquid(tail)
    tail_ret = S._returns(tail_close)

    cases = (
        (S._sma, ret, tail_ret, 7, 5),
        (S._std, ret, tail_ret, 14, 7),
        (S._sma, close, tail_close, 12, 8),
        (S._sma, close, tail_close, 48, 24),
    )
    for fn, full_x, tail_x, n, m in cases:
        expected = fn(full_x, n, m).sel(time=dt)
        got = fn(tail_x, n, m).sel(time=dt)
        np.testing.assert_allclose(got.values, expected.values, atol=0.0, rtol=0.0)
