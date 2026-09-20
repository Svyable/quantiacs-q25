from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "strategies/generated/q25_refinement_ensemble.py"
SPEC = importlib.util.spec_from_file_location("q25_refinement_ensemble_test", PATH)
assert SPEC and SPEC.loader
S = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(S)

from submissions import q25_sharpe7_vol2_multipass as FROZEN


def _panel(days: int = 900, assets: int = 10, seed: int = 23) -> xr.DataArray:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2018-01-01", periods=days, freq="D")
    ret = rng.normal(0.00045, 0.03, (days, assets))
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
    liquid = data.sel(field="is_liquid").transpose("time", "asset")
    for mode in (
        "base_sharpe7",
        "terminal",
        "vote4",
        "single_path",
        "anti_quality",
        "ensemble",
    ):
        w = S.calculate_weights(data, mode)
        assert np.isfinite(w.values).all()
        assert float(w.min()) >= -1e-12
        assert float(w.max()) <= S.NAME_CAP + 1e-12
        assert float(w.sum("asset").max()) <= 1.0 + 1e-12
        assert float((w * (1.0 - liquid)).max()) <= 1e-12


def test_ensemble_is_prefix_causal():
    data = _panel()
    full = S.calculate_weights(data, "ensemble")
    for cut in (300, 600, 899):
        got = S.calculate_weights(data.isel(time=slice(0, cut + 1)), "ensemble")
        np.testing.assert_allclose(
            got.values,
            full.isel(time=slice(0, cut + 1)).values,
            atol=1e-12,
            rtol=0.0,
        )


def test_ensemble_is_asset_order_invariant():
    data = _panel()
    expected = S.calculate_weights(data, "ensemble")
    rev = data.sel(asset=list(reversed(data.asset.values)))
    got = S.calculate_weights(rev, "ensemble").sel(asset=data.asset.values)
    np.testing.assert_allclose(got.values, expected.values, atol=1e-12, rtol=0.0)


def test_path_states_are_monotone_refinements():
    data = _panel(400)
    liquid, root, predicates, _ = S._features(data)
    assert bool((root <= liquid + 1e-12).all())
    for order in (S.PATH_A, S.PATH_B):
        prev = root
        for state in S._path_states(root, predicates, order):
            assert bool((state <= prev + 1e-12).all())
            prev = state


def test_ensemble_is_exact_equal_average_of_nine_smoothed_books():
    data = _panel(500)
    liquid, root, predicates, score = S._features(data)
    states = [root]
    states += S._path_states(root, predicates, S.PATH_A)
    states += S._path_states(root, predicates, S.PATH_B)
    books = [S._state_portfolio(score, state, liquid) for state in states]
    expected = S._sma(sum(books) / 9.0, 3, 1) * liquid
    got = S.calculate_weights(data, "ensemble")
    np.testing.assert_allclose(got.values, expected.values, atol=0.0, rtol=0.0)


def test_controls_are_mechanically_distinct():
    data = _panel()
    outputs = {
        mode: S.calculate_weights(data, mode).values
        for mode in ("terminal", "vote4", "single_path", "anti_quality", "ensemble")
    }
    assert np.max(np.abs(outputs["ensemble"] - outputs["terminal"])) > 1e-8
    assert np.max(np.abs(outputs["ensemble"] - outputs["vote4"])) > 1e-8
    assert np.max(np.abs(outputs["ensemble"] - outputs["single_path"])) > 1e-8
    assert np.max(np.abs(outputs["ensemble"] - outputs["anti_quality"])) > 1e-8
