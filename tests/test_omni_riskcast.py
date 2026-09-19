from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "strategies/generated/q25_omni_riskcast_sharpe7.py"
SPEC = importlib.util.spec_from_file_location("omni_riskcast_test", PATH)
assert SPEC and SPEC.loader
S = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(S)

from submissions import q25_sharpe7_vol2_multipass as FROZEN


def _panel(days: int, assets: int, seed: int, stock: bool = False) -> xr.DataArray:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2018-01-01", periods=days, freq="D")
    ret = rng.normal(0.0002 if stock else 0.0004, 0.012 if stock else 0.03, (days, assets))
    close = 100.0 * np.exp(np.cumsum(ret, axis=0))
    op = close * np.exp(rng.normal(0.0, 0.002, (days, assets)))
    high = np.maximum(op, close) * (1.0 + np.abs(rng.normal(0.0, 0.004, (days, assets))))
    low = np.minimum(op, close) * (1.0 - np.abs(rng.normal(0.0, 0.004, (days, assets))))
    vol = np.exp(rng.normal(10.0, 1.0, (days, assets)))
    liq = np.ones((days, assets))
    values = np.stack([op, high, low, close, vol, liq], axis=0)
    return xr.DataArray(
        values,
        dims=("field", "time", "asset"),
        coords={
            "field": ["open", "high", "low", "close", "vol", "is_liquid"],
            "time": idx,
            "asset": [f"A{i:03d}" for i in range(assets)],
        },
        name="stock" if stock else "cryptodaily",
    )


def _data(days: int = 1050):
    return {
        "crypto": _panel(days, 10, 17, False),
        "spx": _panel(days, 36, 23, True),
        "ndx": _panel(days, 32, 29, True),
    }


def test_self_contained_carrier_matches_frozen_sharpe7():
    data = _data(500)
    got = S._sharpe7_carrier(data["crypto"])
    expected = FROZEN.strategy(data["crypto"], {"window": 7}, "base")
    np.testing.assert_allclose(got.values, expected.values, atol=0.0, rtol=0.0)


def test_all_modes_respect_long_only_caps():
    data = _data()
    for mode in ("base", "static_median", "dynamic_ungated", "inverted", "dynamic"):
        w = S.calculate_weights(data, mode)
        assert np.isfinite(w.values).all()
        assert float(w.min()) >= -1e-12
        assert float(w.max()) <= 0.25 + 1e-12
        assert float(w.sum("asset").max()) <= 1.0 + 1e-12


def test_dynamic_is_prefix_causal():
    data = _data()
    full = S.calculate_weights(data, "dynamic")
    for cut in (780, 900, 1049):
        prefix = {k: v.isel(time=slice(0, cut + 1)) for k, v in data.items()}
        got = S.calculate_weights(prefix, "dynamic")
        np.testing.assert_allclose(
            got.values,
            full.isel(time=slice(0, cut + 1)).values,
            atol=1e-12,
            rtol=0.0,
        )


def test_zero_health_means_exact_desired_abstention():
    data = _data()
    idx = pd.DatetimeIndex(data["crypto"].time.values)
    experts = S._expert_panel(data["spx"], data["ndx"], idx)
    target = S._future_downside_target(data["crypto"])
    state = S._dynamic_risk_state(experts, target)
    desired = S._desired_scale(state, "dynamic")
    zero = state["health"].eq(0.0)
    assert zero.any()
    np.testing.assert_allclose(desired.loc[zero].values, 1.0, atol=0.0, rtol=0.0)


def test_controls_are_mechanically_distinct_after_warmup():
    data = _data()
    static = S.calculate_weights(data, "static_median").values
    ungated = S.calculate_weights(data, "dynamic_ungated").values
    inverted = S.calculate_weights(data, "inverted").values
    dynamic = S.calculate_weights(data, "dynamic").values
    assert np.max(np.abs(static - ungated)) > 1e-8
    assert np.max(np.abs(inverted - dynamic)) > 1e-8
