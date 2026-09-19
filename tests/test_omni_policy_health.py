from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "strategies/generated/q25_omni_policy_health_sharpe7.py"
SPEC = importlib.util.spec_from_file_location("omni_policy_health_test", PATH)
assert SPEC and SPEC.loader
S = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(S)

from submissions import q25_sharpe7_vol2_multipass as FROZEN


def _panel(days: int, assets: int, seed: int, stock: bool = False) -> xr.DataArray:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2018-01-01", periods=days, freq="D")
    ret = rng.normal(0.00015 if stock else 0.0004, 0.012 if stock else 0.03, (days, assets))
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


def _data(days: int = 1100):
    return {
        "crypto": _panel(days, 10, 101, False),
        "spx": _panel(days, 34, 103, True),
        "ndx": _panel(days, 31, 107, True),
    }


def test_self_contained_carrier_matches_promoted_sharpe7_exactly():
    data = _data(500)
    got = S._sharpe7_carrier(data["crypto"])
    expected = FROZEN.strategy(data["crypto"], {"window": 7}, "base")
    np.testing.assert_allclose(got.values, expected.values, atol=0.0, rtol=0.0)


def test_modes_respect_long_only_name_and_gross_caps():
    data = _data()
    for mode in ("base", "always_static", "fast_only", "slow_only", "inverted_dual", "dual"):
        w = S.calculate_weights(data, mode)
        assert np.isfinite(w.values).all()
        assert float(w.min()) >= -1e-12
        assert float(w.max()) <= 0.25 + 1e-12
        assert float(w.sum("asset").max()) <= 1.0 + 1e-12


def test_dual_mode_is_prefix_causal():
    data = _data()
    full = S.calculate_weights(data, "dual")
    for cut in (800, 950, 1099):
        prefix = {k: v.isel(time=slice(0, cut + 1)) for k, v in data.items()}
        got = S.calculate_weights(prefix, "dual")
        np.testing.assert_allclose(
            got.values,
            full.isel(time=slice(0, cut + 1)).values,
            atol=1e-12,
            rtol=0.0,
        )


def test_policy_health_uses_previous_day_weights():
    data = _data(500)
    base = S._sharpe7_carrier(data["crypto"])
    actual = S._hypothetical_policy_return(data["crypto"], base)
    close = S._field(data["crypto"], "close")
    ret = (close / close.shift(1) - 1.0).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    expected = (base.to_pandas().shift(1).fillna(0.0) * ret).sum(axis=1)
    np.testing.assert_allclose(actual.values, expected.values, atol=0.0, rtol=0.0)


def test_weekly_choice_only_changes_on_mondays():
    idx = pd.date_range("2024-01-01", periods=70, freq="D")
    state = pd.DataFrame(index=idx)
    toggle = np.arange(len(idx)) % 3 == 0
    state["fast_better"] = toggle
    state["slow_better"] = np.roll(toggle, 1)
    state["base_fast"] = 0.0
    state["static_fast"] = np.where(state["fast_better"], 1.0, -1.0)
    state["base_slow"] = 0.0
    state["static_slow"] = np.where(state["slow_better"], 1.0, -1.0)
    choice = S._weekly_choice(state, "dual")
    changed = choice.ne(choice.shift(1)).fillna(False)
    assert all(pd.Timestamp(dt).dayofweek == 0 for dt in choice.index[changed])


def test_controls_are_mechanically_distinct_after_warmup():
    data = _data()
    outputs = {
        mode: S.calculate_weights(data, mode).values
        for mode in ("base", "always_static", "fast_only", "slow_only", "inverted_dual", "dual")
    }
    assert np.max(np.abs(outputs["base"] - outputs["always_static"])) > 1e-8
    assert np.max(np.abs(outputs["dual"] - outputs["inverted_dual"])) > 1e-8
