from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
RESEARCH_PATH = ROOT / "strategies/generated/q25_pareto_skyline.py"
SUBMISSION_PATH = ROOT / "submissions/q25_pareto_skyline_multipass.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


R = _load(RESEARCH_PATH, "pareto_research")
S = _load(SUBMISSION_PATH, "pareto_submission")


def _panel(days=600, assets=10, seed=31):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2019-01-01", periods=days, freq="D")
    ret = rng.normal(0.00045, 0.03, (days, assets))
    close = 100.0 * np.exp(np.cumsum(ret, axis=0))
    op = close * np.exp(rng.normal(0.0, 0.003, (days, assets)))
    high = np.maximum(op, close) * (1.0 + np.abs(rng.normal(0.0, 0.006, (days, assets))))
    low = np.minimum(op, close) * (1.0 - np.abs(rng.normal(0.0, 0.006, (days, assets))))
    vol = np.exp(rng.normal(10.0, 1.0, (days, assets)))
    liq = np.ones((days, assets))
    return xr.DataArray(
        np.stack([op, high, low, close, vol, liq]),
        dims=("field", "time", "asset"),
        coords={
            "field": ["open", "high", "low", "close", "vol", "is_liquid"],
            "time": idx,
            "asset": [f"A{i:03d}" for i in range(assets)],
        },
    )


def test_submission_bytes_equal_research_bytes():
    assert SUBMISSION_PATH.read_bytes() == RESEARCH_PATH.read_bytes()


def test_submission_strategy_exactly_matches_research_strategy():
    data = _panel()
    got = S.strategy(data)
    expected = R.strategy(data)
    np.testing.assert_allclose(got.values, expected.values, atol=0.0, rtol=0.0)


def test_submission_is_admissible_on_synthetic_panel():
    w = S.strategy(_panel())
    assert np.isfinite(w.values).all()
    assert float(w.min()) >= -1e-12
    assert float(w.max()) <= S.NAME_CAP + 1e-12
    assert float(w.sum("asset").max()) <= 1.0 + 1e-12
