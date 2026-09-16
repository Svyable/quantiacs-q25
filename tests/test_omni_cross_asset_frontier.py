from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr


PATH = Path("strategies/generated/omni_cross_asset_frontier.py")
spec = importlib.util.spec_from_file_location("omni_frontier", PATH)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _panel(seed: int = 4, periods: int = 900, assets: int = 24) -> xr.DataArray:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2013-01-02", periods=periods)
    common = rng.normal(0.0002, 0.009, size=(periods, 1))
    noise = rng.normal(0.0, 0.012, size=(periods, assets))
    ret = 0.65 * common + 0.35 * noise
    close = 100.0 * np.exp(np.cumsum(ret, axis=0))
    liquid = np.ones_like(close)
    values = np.stack([close, liquid], axis=0)
    return xr.DataArray(values, dims=("field", "time", "asset"), coords={"field":["close","is_liquid"], "time":dates, "asset":[f"S{i:03d}" for i in range(assets)]})


def _crypto(seed: int = 7, start: str = "2013-01-01", periods: int = 1500, assets: int = 8) -> xr.DataArray:
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start, periods=periods, freq="D")
    common = rng.normal(0.0005, 0.025, size=(periods, 1))
    noise = rng.normal(0.0, 0.03, size=(periods, assets))
    ret = 0.7 * common + 0.3 * noise
    close = 50.0 * np.exp(np.cumsum(ret, axis=0))
    liquid = np.ones_like(close)
    values = np.stack([close, liquid], axis=0)
    return xr.DataArray(values, dims=("field", "time", "asset"), coords={"field":["close","is_liquid"], "time":dates, "asset":[f"C{i:02d}" for i in range(assets)]})


def test_tail_and_fragility_are_bounded_and_prefix_invariant():
    stocks = _panel()
    end = pd.Timestamp(stocks.time.values[820])
    full_ctx = mod._stock_context(stocks)
    cut = stocks.sel(time=slice(None, end))
    cut_ctx = mod._stock_context(cut)

    for fn in (mod._tail_dependence, mod._fragility_recovery):
        full = fn(full_ctx)
        short = fn(cut_ctx)
        for key in ("primary", "ablation", "inverted"):
            assert short[key].dropna().between(0.0, 1.0).all()
            left = float(full[key].loc[end])
            right = float(short[key].loc[end])
            assert np.isclose(left, right, atol=1e-12, rtol=0.0, equal_nan=True)


def test_online_ridge_uses_only_realized_labels():
    stocks = _panel(periods=850)
    crypto = _crypto(periods=1500)
    end = pd.Timestamp(stocks.time.values[800])
    full_ctx = mod._stock_context(stocks)
    full = mod._online_ridge(full_ctx, crypto)

    cut_stocks = stocks.sel(time=slice(None, end))
    cut_crypto = crypto.sel(time=slice(None, end))
    cut = mod._online_ridge(mod._stock_context(cut_stocks), cut_crypto)

    for key in ("primary", "ablation", "inverted"):
        left = float(full[key].loc[end])
        right = float(cut[key].loc[end])
        assert np.isclose(left, right, atol=1e-12, rtol=0.0, equal_nan=True)
        assert 0.0 <= right <= 1.0


def test_risk_scaling_never_adds_exposure():
    dates = pd.date_range("2020-01-01", periods=10, freq="D")
    assets = ["A", "B", "C", "D"]
    base = xr.DataArray(np.full((10, 4), 0.25), dims=("time", "asset"), coords={"time":dates, "asset":assets})
    risk = pd.Series(np.linspace(0.0, 1.0, 10), index=dates)
    out = mod._risk_to_weights(base, risk)
    assert np.isfinite(out.values).all()
    assert (out.values >= 0.0).all()
    assert (out.values <= 0.25 + 1e-12).all()
    assert (out.sum("asset").values <= 1.0 + 1e-12).all()
    assert float(out.sum("asset").isel(time=-1)) <= 0.2500000001
