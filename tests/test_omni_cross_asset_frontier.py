from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr


FROZEN_PATH = Path("strategies/generated/omni_cross_asset_frontier.py")
frozen_spec = importlib.util.spec_from_file_location("omni_frontier_frozen", FROZEN_PATH)
assert frozen_spec is not None and frozen_spec.loader is not None
frozen_mod = importlib.util.module_from_spec(frozen_spec)
frozen_spec.loader.exec_module(frozen_mod)

REPAIRED_PATH = Path("strategies/generated/omni_cross_asset_frontier_r1.py")
repaired_spec = importlib.util.spec_from_file_location("omni_frontier_repaired", REPAIRED_PATH)
assert repaired_spec is not None and repaired_spec.loader is not None
mod = importlib.util.module_from_spec(repaired_spec)
repaired_spec.loader.exec_module(mod)

REPAIR_RECORD = Path("experiments/omni_cross_asset_frontier_20260915r1/repair_record.json")


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


def test_frozen_wave1_preserves_documented_pre_market_dtype_failure():
    """Keep the original freeze immutable and prove why R1 exists."""
    record = json.loads(REPAIR_RECORD.read_text())
    assert record["repair_class"] == "IMPLEMENTATION_ONLY_PRE_MARKET"
    assert record["market_returns_observed_for_wave1_before_repair"] is False
    assert record["formula_changed"] is False
    assert record["parameter_changed"] is False
    assert record["window_changed"] is False
    assert record["threshold_changed"] is False
    assert record["selection_rule_changed"] is False
    assert record["portfolio_rule_changed"] is False
    assert "object-dtype" in record["failure"]

    stocks = _panel()
    ctx = frozen_mod._stock_context(stocks)
    with pytest.raises(TypeError):
        frozen_mod._tail_dependence(ctx)


def test_repaired_tail_and_fragility_are_bounded_and_prefix_invariant():
    stocks = _panel()
    end = pd.Timestamp(stocks.time.values[820])
    full_ctx = mod._stock_context(stocks)
    cut_ctx = mod._stock_context(stocks.sel(time=slice(None, end)))
    for fn in (mod._tail_dependence, mod._fragility_recovery):
        full = fn(full_ctx)
        short = fn(cut_ctx)
        for key in ("primary", "ablation", "inverted"):
            assert short[key].dropna().between(0.0, 1.0).all()
            left = float(full[key].loc[end])
            right = float(short[key].loc[end])
            assert np.isclose(left, right, atol=1e-12, rtol=0.0, equal_nan=True)


def test_online_ridge_uses_only_realized_labels_after_repair():
    stocks = _panel(periods=850)
    crypto = _crypto(periods=1500)
    end = pd.Timestamp(stocks.time.values[800])
    full = mod._online_ridge(mod._stock_context(stocks), crypto)
    cut = mod._online_ridge(
        mod._stock_context(stocks.sel(time=slice(None, end))),
        crypto.sel(time=slice(None, end)),
    )

    for key in ("primary", "ablation", "inverted"):
        left = float(full[key].loc[end])
        right = float(cut[key].loc[end])
        assert np.isclose(left, right, atol=1e-12, rtol=0.0, equal_nan=True)
        assert 0.0 <= right <= 1.0


def test_risk_scaling_never_adds_exposure_after_repair():
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
