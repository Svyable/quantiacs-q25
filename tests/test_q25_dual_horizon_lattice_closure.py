from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "strategies/generated/q25_dual_horizon_lattice_closure.py"
SPEC = importlib.util.spec_from_file_location("q25_dual_horizon_lattice_closure_test", PATH)
assert SPEC and SPEC.loader
S = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(S)


def _panel(days: int = 900, assets: int = 10, seed: int = 23) -> xr.DataArray:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2018-01-01", periods=days, freq="D")
    ret = rng.normal(0.00045, 0.03, (days, assets))
    close = 100.0 * np.exp(np.cumsum(ret, axis=0))
    op = close * np.exp(rng.normal(0.0, 0.003, (days, assets)))
    high = np.maximum(op, close) * (1.0 + np.abs(rng.normal(0.0, 0.006, (days, assets))))
    low = np.minimum(op, close) * (1.0 - np.abs(rng.normal(0.0, 0.006, (days, assets))))
    volume = np.exp(rng.normal(10.0, 1.0, (days, assets)))
    liquid = np.ones((days, assets))
    values = np.stack([op, high, low, close, volume, liquid], axis=0)
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


def test_base_control_matches_frozen_pareto_incumbent_when_available():
    try:
        from strategies.generated import q25_pareto_skyline as incumbent
    except ImportError:
        pytest.skip("incumbent module is present in the full repository")
    data = _panel()
    got = S.calculate_weights(data, "base_pareto")
    expected = incumbent.calculate_weights(data, "pareto_le1")
    np.testing.assert_allclose(got.values, expected.values, atol=0.0, rtol=0.0)


def test_all_modes_are_admissible_and_mechanically_distinct():
    data = _panel()
    liquid = data.sel(field="is_liquid").transpose("time", "asset")
    outputs = {}
    modes = (
        "base_pareto",
        "root_only",
        "meet_only",
        "join_only",
        "slow_only",
        "anti_slow",
        "closure",
    )
    for mode in modes:
        w = S.calculate_weights(data, mode)
        outputs[mode] = w.values
        assert np.isfinite(w.values).all()
        assert float(w.min()) >= -1e-12
        assert float(w.max()) <= S.NAME_CAP + 1e-12
        assert float(w.sum("asset").max()) <= 1.0 + 1e-12
        assert float((w * (1.0 - liquid)).max()) <= 1e-12
    assert np.max(np.abs(outputs["closure"] - outputs["base_pareto"])) > 1e-8
    assert np.max(np.abs(outputs["closure"] - outputs["meet_only"])) > 1e-8
    assert np.max(np.abs(outputs["closure"] - outputs["join_only"])) > 1e-8
    assert np.max(np.abs(outputs["closure"] - outputs["anti_slow"])) > 1e-8


def test_lattice_state_relations_hold():
    data = _panel(500)
    (
        _liquid,
        _score,
        root,
        _base_fast,
        fast,
        slow,
        meet,
        join,
        _slow_counts,
    ) = S._states(data)
    assert bool((meet.astype(int) <= fast.astype(int)).all())
    assert bool((meet.astype(int) <= slow.astype(int)).all())
    assert bool((fast.astype(int) <= join.astype(int)).all())
    assert bool((slow.astype(int) <= join.astype(int)).all())
    assert bool((join.astype(int) <= root.astype(int)).all())


def test_resolver_prefers_meet_then_join_then_root():
    time = pd.date_range("2025-01-01", periods=3, freq="D")
    assets = [f"A{i}" for i in range(6)]
    coords = {"time": time, "asset": assets}
    root = xr.DataArray(
        [[1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1]],
        dims=("time", "asset"),
        coords=coords,
    ).astype(bool)
    # t0: meet has 4 => choose meet.
    # t1: meet has 2, join has 4 => choose join.
    # t2: meet has 2, join has 3 => choose root.
    meet = xr.DataArray(
        [[1, 1, 1, 1, 0, 0], [1, 1, 0, 0, 0, 0], [1, 1, 0, 0, 0, 0]],
        dims=("time", "asset"),
        coords=coords,
    ).astype(bool)
    join = xr.DataArray(
        [[1, 1, 1, 1, 1, 0], [1, 1, 1, 1, 0, 0], [1, 1, 1, 0, 0, 0]],
        dims=("time", "asset"),
        coords=coords,
    ).astype(bool)
    got = S._resolve(root, meet, join)
    np.testing.assert_allclose(got.isel(time=0).values, meet.isel(time=0).values)
    np.testing.assert_allclose(got.isel(time=1).values, join.isel(time=1).values)
    np.testing.assert_allclose(got.isel(time=2).values, root.isel(time=2).values)


def test_closure_is_prefix_causal():
    data = _panel()
    full = S.calculate_weights(data, "closure")
    for cut in (300, 600, 899):
        got = S.calculate_weights(data.isel(time=slice(0, cut + 1)), "closure")
        np.testing.assert_allclose(
            got.values,
            full.isel(time=slice(0, cut + 1)).values,
            atol=1e-12,
            rtol=0.0,
        )


def test_closure_is_asset_order_invariant():
    data = _panel()
    expected = S.calculate_weights(data, "closure")
    reversed_data = data.sel(asset=list(reversed(data.asset.values)))
    got = S.calculate_weights(reversed_data, "closure").sel(asset=data.asset.values)
    np.testing.assert_allclose(got.values, expected.values, atol=1e-12, rtol=0.0)


def test_terminal_365_day_bounded_replay_is_exact():
    data = _panel(1000)
    full = S.calculate_weights(data, "closure")
    tail = S.calculate_weights(data.isel(time=slice(-365, None)), "closure")
    np.testing.assert_allclose(
        tail.isel(time=-1).values,
        full.isel(time=-1).values,
        atol=1e-12,
        rtol=0.0,
    )
