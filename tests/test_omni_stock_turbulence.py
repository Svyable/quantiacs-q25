from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "strategies"
    / "generated"
    / "omni_stock_turbulence_ic_overlay.py"
)
SPEC = importlib.util.spec_from_file_location("omni_stock_turbulence", MODULE_PATH)
assert SPEC and SPEC.loader
omni = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(omni)


def _market_data(
    dates: pd.DatetimeIndex,
    assets: list[str],
    seed: int,
) -> xr.DataArray:
    rng = np.random.default_rng(seed)
    n, m = len(dates), len(assets)
    returns = rng.normal(0.0004, 0.02, size=(n, m))
    close = 100.0 * np.exp(np.cumsum(returns, axis=0))
    high = close * (1.0 + rng.uniform(0.001, 0.02, size=(n, m)))
    low = close * (1.0 - rng.uniform(0.001, 0.02, size=(n, m)))
    open_ = close * np.exp(rng.normal(0.0, 0.003, size=(n, m)))
    volume = rng.lognormal(12.0, 0.5, size=(n, m))
    liquid = np.ones((n, m), dtype=float)

    values = np.stack([open_, high, low, close, volume, liquid], axis=0)
    return xr.DataArray(
        values,
        dims=("field", "time", "asset"),
        coords={
            "field": ["open", "high", "low", "close", "vol", "is_liquid"],
            "time": dates,
            "asset": assets,
        },
    )


@pytest.fixture(scope="module")
def synthetic_data() -> dict[str, xr.DataArray]:
    crypto_dates = pd.date_range("2013-01-01", periods=1_100, freq="D")
    stock_dates = pd.bdate_range("2013-01-01", periods=800)
    return {
        "crypto": _market_data(crypto_dates, [f"C{i}" for i in range(10)], seed=1),
        "stocks": _market_data(stock_dates, [f"S{i}" for i in range(40)], seed=2),
    }


def test_omni_constraints_and_controls(synthetic_data):
    gated = omni.calculate_weights(synthetic_data, mode="gated")
    assert set(gated.dims) == {"time", "asset"}
    assert np.isfinite(gated.values).all()
    assert float(gated.min()) >= -1e-12
    assert float(gated.max()) <= omni.NAME_CAP + 1e-12
    assert float(gated.sum("asset").max()) <= 1.0 + 1e-10

    base = omni.calculate_weights(synthetic_data, mode="base")
    ungated = omni.calculate_weights(synthetic_data, mode="ungated")
    inverted = omni.calculate_weights(synthetic_data, mode="inverted")

    for weights in (base, ungated, inverted):
        assert np.isfinite(weights.values).all()
        assert float(weights.min()) >= -1e-12
        assert float(weights.max()) <= omni.NAME_CAP + 1e-12
        assert float(weights.sum("asset").max()) <= 1.0 + 1e-10

    # Controls are mechanically distinct on deterministic synthetic data.
    assert float(abs(base - ungated).max()) > 0.0
    assert float(abs(gated - inverted).max()) > 0.0


def test_omni_prefix_invariance(synthetic_data):
    crypto = synthetic_data["crypto"]
    stocks = synthetic_data["stocks"]
    cut = 950
    cutoff = pd.Timestamp(crypto.time.values[cut - 1])

    prefix = {
        "crypto": crypto.isel(time=slice(0, cut)),
        "stocks": stocks.sel(time=slice(None, cutoff)),
    }

    prefix_weights = omni.calculate_weights(prefix, mode="gated")
    full_weights = omni.calculate_weights(synthetic_data, mode="gated").sel(
        time=prefix_weights.time
    )
    max_error = float(abs(prefix_weights - full_weights).max())
    assert max_error < 1e-10


def test_overlay_abstains_when_ic_health_is_zero():
    idx = pd.date_range("2026-01-01", periods=5, freq="D")
    diagnostics = pd.DataFrame(
        {
            "turbulence": [0.95] * 5,
            "consensus": [1.0] * 5,
            "health": [0.0] * 5,
        },
        index=idx,
    )
    scale = omni._overlay_scale(diagnostics, mode="gated")
    assert np.allclose(scale.to_numpy(), 1.0)

    ungated = omni._overlay_scale(diagnostics, mode="ungated")
    assert bool((ungated < 1.0).all())
    assert bool((ungated >= omni.RISK_FLOOR).all())
