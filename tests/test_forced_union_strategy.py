import importlib.util
from pathlib import Path

import numpy as np
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fixture(seed=25, days=180, assets=7):
    rng = np.random.default_rng(seed)
    time = np.arange(np.datetime64("2024-01-01"), np.datetime64("2024-01-01") + days)
    names = np.array([f"A{i}" for i in range(assets)])
    rets = rng.normal(0.0008, 0.025, (days, assets))
    close = 100 * np.exp(np.cumsum(rets, axis=0))
    liquid = np.ones_like(close)
    data = np.stack([close, liquid], axis=0)
    return xr.DataArray(data, dims=("field", "time", "asset"), coords={"field": ["close", "is_liquid"], "time": time, "asset": names})


def test_forced_union_matches_frozen_parent_join_only():
    candidate = _load("strategies/generated/q25_forced_union.py", "forced_union")
    parent = _load("strategies/generated/q25_dual_horizon_lattice_closure.py", "lattice")
    data = _fixture()
    got = candidate.calculate_weights(data)
    expected = parent.calculate_weights(data, "join_only")
    xr.testing.assert_allclose(got, expected, rtol=0, atol=1e-12)


def test_forced_union_is_long_only_liquid_capped_and_order_invariant():
    candidate = _load("strategies/generated/q25_forced_union.py", "forced_union_invariants")
    data = _fixture(days=200)
    data.loc[{"field": "is_liquid", "time": data.time[-20:], "asset": "A2"}] = 0
    w = candidate.calculate_weights(data)
    assert float(w.min()) >= -1e-15
    assert float(w.max()) <= 0.25 + 1e-15
    assert float(w.sum("asset").max()) <= 1.0 + 1e-12
    assert float(abs(w.sel(asset="A2", time=data.time[-20:])).max()) == 0.0
    reversed_data = data.sel(asset=data.asset.values[::-1])
    wr = candidate.calculate_weights(reversed_data).sel(asset=data.asset.values)
    xr.testing.assert_allclose(w, wr, rtol=0, atol=1e-12)


def test_forced_union_prefix_causality():
    candidate = _load("strategies/generated/q25_forced_union.py", "forced_union_prefix")
    data = _fixture(days=210)
    cut = 170
    full = candidate.calculate_weights(data).isel(time=slice(0, cut))
    prefix = candidate.calculate_weights(data.isel(time=slice(0, cut)))
    xr.testing.assert_allclose(full, prefix, rtol=0, atol=1e-12)
