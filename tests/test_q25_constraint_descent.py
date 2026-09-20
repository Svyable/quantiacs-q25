from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "strategies/generated/q25_constraint_descent.py"
SPEC = importlib.util.spec_from_file_location("q25_constraint_descent_test", PATH)
assert SPEC and SPEC.loader
S = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(S)

from submissions import q25_sharpe7_vol2_multipass as FROZEN


def _panel(days: int = 900, assets: int = 10, seed: int = 17) -> xr.DataArray:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2018-01-01", periods=days, freq="D")
    ret = rng.normal(0.0005, 0.03, (days, assets))
    close = 100.0 * np.exp(np.cumsum(ret, axis=0))
    op = close * np.exp(rng.normal(0.0, 0.003, (days, assets)))
    high = np.maximum(op, close) * (1.0 + np.abs(rng.normal(0.0, 0.006, (days, assets))))
    low = np.minimum(op, close) * (1.0 - np.abs(rng.normal(0.0, 0.006, (days, assets))))
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
        name="cryptodaily",
    )


def test_base_control_matches_promoted_sharpe7_exactly():
    data = _panel()
    got = S.calculate_weights(data, "base_sharpe7")
    expected = FROZEN.strategy(data, {"window": 7}, "base")
    np.testing.assert_allclose(got.values, expected.values, atol=0.0, rtol=0.0)


def test_all_modes_are_admissible():
    data = _panel()
    modes = (
        "base_sharpe7",
        "forced_all",
        "vote4",
        "reverse_descent",
        "anti_quality",
        "descent",
    )
    liquid = data.sel(field="is_liquid").transpose("time", "asset")
    for mode in modes:
        w = S.calculate_weights(data, mode)
        assert np.isfinite(w.values).all()
        assert float(w.min()) >= -1e-12
        assert float(w.max()) <= S.NAME_CAP + 1e-12
        assert float(w.sum("asset").max()) <= 1.0 + 1e-12
        assert float((w * (1.0 - liquid)).max()) <= 1e-12


def test_descent_is_prefix_causal():
    data = _panel()
    full = S.calculate_weights(data, "descent")
    for cut in (300, 600, 899):
        prefix = data.isel(time=slice(0, cut + 1))
        got = S.calculate_weights(prefix, "descent")
        np.testing.assert_allclose(
            got.values,
            full.isel(time=slice(0, cut + 1)).values,
            atol=1e-12,
            rtol=0.0,
        )


def test_descent_is_asset_order_invariant():
    data = _panel()
    base = S.calculate_weights(data, "descent")
    reversed_data = data.sel(asset=list(reversed(data.asset.values)))
    got = S.calculate_weights(reversed_data, "descent").sel(asset=data.asset.values)
    np.testing.assert_allclose(got.values, base.values, atol=1e-12, rtol=0.0)


def test_refinement_never_expands_candidate_set():
    data = _panel(300)
    _, liquid, _, predicates = S._features(data)
    mask = liquid
    for name in ("quality", "trend", "drawdown", "momentum", "volatility"):
        nxt = S._refine(mask, predicates[name], S.MIN_SURVIVORS)
        assert bool((nxt <= mask + 1e-12).all())
        mask = nxt


def test_refinement_abstains_when_rule_would_overprune():
    idx = pd.date_range("2025-01-01", periods=2)
    assets = ["A", "B", "C", "D"]
    mask = xr.DataArray(
        np.ones((2, 4)),
        dims=("time", "asset"),
        coords={"time": idx, "asset": assets},
    )
    pred = xr.DataArray(
        np.array([[1, 1, 0, 0], [1, 1, 1, 0]], dtype=float),
        dims=("time", "asset"),
        coords={"time": idx, "asset": assets},
    )
    got = S._refine(mask, pred, 3.0)
    np.testing.assert_allclose(got.isel(time=0).values, np.ones(4))
    np.testing.assert_allclose(got.isel(time=1).values, np.array([1, 1, 1, 0], dtype=float))


def test_controls_are_mechanically_distinct():
    data = _panel()
    outputs = {
        mode: S.calculate_weights(data, mode).values
        for mode in ("forced_all", "vote4", "reverse_descent", "anti_quality", "descent")
    }
    assert np.max(np.abs(outputs["descent"] - outputs["forced_all"])) > 1e-8
    assert np.max(np.abs(outputs["descent"] - outputs["vote4"])) > 1e-8
    assert np.max(np.abs(outputs["descent"] - outputs["reverse_descent"])) > 1e-8
    assert np.max(np.abs(outputs["descent"] - outputs["anti_quality"])) > 1e-8
