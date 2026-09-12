from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from research.benchmark import check_causality

ROOT = Path(__file__).resolve().parents[1]

CASES = [
    ("ebenezar_20260912_sharpe3_vol_guard.py", 3),
    ("ebenezar_20260912_sharpe7_vol2.py", 7),
    ("ebenezar_20260912_dual_sharpe_classifier.py", 7),
    ("ebenezar_20260912_sharpe_acceleration.py", 3),
    ("ebenezar_20260912_residual_sharpe.py", 7),
    ("ebenezar_20260912_lattice_consensus.py", 7),
    ("ebenezar_20260912_sharpe_pullback_reentry.py", 21),
]


def _panel() -> xr.DataArray:
    rng = np.random.default_rng(20260912)
    n_time, n_asset = 430, 10
    time = pd.date_range("2018-01-01", periods=n_time, freq="D")
    asset = [f"A{i}" for i in range(n_asset)]
    ret = rng.normal(0.0004, 0.025, (n_time, n_asset))
    close = 100.0 * np.exp(np.cumsum(ret, axis=0))
    open_ = close * np.exp(rng.normal(0.0, 0.002, close.shape))
    high = np.maximum(open_, close) * 1.005
    low = np.minimum(open_, close) * 0.995
    volume = np.exp(rng.normal(10.0, 0.7, close.shape))
    liquid = np.ones_like(close)
    values = np.stack([open_, high, low, close, volume, liquid], axis=0)
    return xr.DataArray(
        values,
        dims=("field", "time", "asset"),
        coords={
            "field": ["open", "high", "low", "close", "vol", "is_liquid"],
            "time": time,
            "asset": asset,
        },
        name="cryptodaily",
    )


def _load(name: str):
    path = ROOT / "strategies" / "generated" / name
    spec = importlib.util.spec_from_file_location(f"test_{path.stem}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(("name", "window"), CASES)
def test_ebenezar_profiles_return_exact_causal_weight_coordinates(name: str, window: int):
    data = _panel()
    module = _load(name)
    fn = lambda panel: module.strategy(panel, {"window": window}, "base")
    weights = fn(data)

    assert weights.dims == ("time", "asset")
    assert weights.time.equals(data.time)
    assert weights.asset.equals(data.asset)
    assert "field" not in weights.coords
    assert float(weights.max()) <= 0.25 + 1e-12
    assert float(weights.sum("asset").max()) <= 1.0 + 1e-12

    result = check_causality(fn, data, full=weights, checkpoints=3)
    assert result["status"] == "PASS"
