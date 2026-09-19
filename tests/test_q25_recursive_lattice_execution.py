from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from research.benchmark import check_causality

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "strategies" / "generated" / "q25_recursive_lattice_execution.py"


def _load():
    spec = importlib.util.spec_from_file_location("q25_recursive_lattice_execution_test", PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _panel(n_time: int = 520, n_asset: int = 10) -> xr.DataArray:
    rng = np.random.default_rng(20260919)
    time = pd.date_range("2018-01-01", periods=n_time, freq="D")
    asset = [f"A{i}" for i in range(n_asset)]

    common = rng.normal(0.0005, 0.014, (n_time, 1))
    idio = rng.normal(0.0003, 0.018, (n_time, n_asset))
    ret = common + idio
    close = 100.0 * np.exp(np.cumsum(ret, axis=0))
    open_ = close * np.exp(rng.normal(0.0, 0.0025, close.shape))
    span = np.abs(rng.normal(0.009, 0.003, close.shape))
    high = np.maximum(open_, close) * (1.0 + span)
    low = np.minimum(open_, close) * np.maximum(0.01, 1.0 - span)
    volume = np.exp(rng.normal(10.0, 0.65, close.shape))
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


def test_recursive_lattice_mechanics_and_causality():
    module = _load()
    data = _panel()
    weights = module.strategy(data)

    assert weights.dims == ("time", "asset")
    assert weights.time.equals(data.time)
    assert weights.asset.equals(data.asset)
    assert "field" not in weights.coords
    assert float(weights.min()) >= -1e-12
    assert float(weights.max()) <= module.NAME_CAP + 1e-12
    assert float(weights.sum("asset").max()) <= 1.0 + 1e-12

    result = check_causality(module.strategy, data, full=weights, checkpoints=4)
    assert result["status"] == "PASS"
    assert result["max_abs_difference"] <= 1e-10


def test_recursive_lattice_asset_order_invariance():
    module = _load()
    data = _panel()
    normal = module.strategy(data)
    reversed_data = data.sel(asset=list(reversed(data.asset.values)))
    reversed_weights = module.strategy(reversed_data).sel(asset=data.asset)
    assert float(abs(normal - reversed_weights).max()) <= 1e-10


def test_recursive_lattice_forces_liquidity_exit():
    module = _load()
    data = _panel()
    baseline = module.strategy(data)
    held = baseline.isel(time=-2)
    candidate = str(held.asset.values[int(np.argmax(held.values))])

    altered = data.copy(deep=True)
    altered.loc[dict(field="is_liquid", time=altered.time[-1], asset=candidate)] = 0.0
    weights = module.strategy(altered)
    assert float(weights.sel(time=weights.time[-1], asset=candidate)) == 0.0


def test_recursive_lattice_controls_change_deployed_capital():
    module = _load()
    data = _panel()
    central = module.strategy(data)
    base = module.control_weights(data, "base_lattice")
    fixed = module.control_weights(data, "fixed_deadband")
    hysteresis = module.control_weights(data, "hysteresis_atr")

    assert float(abs(central - base).max()) > 1e-8
    assert float(abs(central - fixed).max()) > 1e-8
    assert float(abs(central - hysteresis).max()) > 1e-8


def test_recursive_lattice_terminal_bounded_replay():
    module = _load()
    data = _panel()
    full = module.strategy(data)
    tail = module.strategy(data.isel(time=slice(-365, None)))
    aligned = full.sel(time=tail.time, asset=tail.asset)
    # The state is hard re-anchored every Monday. Ignore the first week of the
    # truncated replay; thereafter recursion has no dependency on earlier state.
    days = pd.DatetimeIndex(tail.time.values)
    first_monday = int(np.flatnonzero(days.dayofweek == module.WEEKLY_REANCHOR_DAY)[0])
    diff = abs(aligned.isel(time=slice(first_monday, None)) - tail.isel(time=slice(first_monday, None)))
    assert float(diff.max()) <= 1e-10
