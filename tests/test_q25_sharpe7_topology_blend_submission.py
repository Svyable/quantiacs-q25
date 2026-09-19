"""Parity and admissibility tests for the frozen Sharpe7 + topology submission."""
import numpy as np
import xarray as xr

from research.benchmark import ROOT, load_module
from test_frontier_c import panel

PROD = ROOT / "submissions/q25_sharpe7_topology_blend_multipass.py"
SH7 = ROOT / "strategies/generated/ebenezar_20260912_sharpe7_vol2.py"
TOPO = ROOT / "strategies/generated/frontier_20260910b_topology_migration.py"


def _latest(w):
    return w.isel(time=-1, drop=True) if "time" in w.dims else w


def _expected(data):
    sh7 = load_module(SH7)
    topo = load_module(TOPO)
    a = _latest(sh7.strategy(data, {"window": 7}, "base"))
    b = _latest(topo.strategy(data, {"window": 84, "top_k": 5}, "base"))
    a, b = xr.align(a, b, join="outer", fill_value=0.0)
    w = 0.5 * a + 0.5 * b
    liquid = data.sel(field="is_liquid").isel(time=-1, drop=True)
    return xr.where((liquid == 1) & (w > 0), w, 0.0).fillna(0.0)


def test_submission_is_exact_frozen_composition():
    data = panel(n=720)
    prod = load_module(PROD)
    got = prod.strategy(data)
    expected = _expected(data)
    xr.testing.assert_allclose(got, expected, atol=1e-12, rtol=0)


def test_submission_is_long_only_liquid_capped_and_cash_safe():
    data = panel(n=720)
    prod = load_module(PROD)
    got = prod.strategy(data)
    assert got.dims == ("asset",)
    assert np.isfinite(got.values).all()
    assert float(got.min()) >= 0.0
    assert float(got.max()) <= 0.25 + 1e-12
    assert float(got.sum()) <= 1.0 + 1e-12
    liquid = data.sel(field="is_liquid").isel(time=-1, drop=True)
    assert float(got.where(liquid != 1, 0.0).sum()) == 0.0


def test_submission_is_asset_order_invariant():
    data = panel(n=720)
    prod = load_module(PROD)
    full = prod.strategy(data)
    shuffled = data.sel(asset=list(reversed(data.asset.values)))
    reordered = prod.strategy(shuffled).sel(asset=data.asset)
    xr.testing.assert_allclose(full, reordered, atol=1e-12, rtol=0)


def test_submission_source_is_self_contained_and_frozen():
    source = PROD.read_text()
    assert "from strategies" not in source
    assert "from research" not in source
    assert "from factory" not in source
    assert "0.5 * a + 0.5 * b" in source
    assert "TOPOLOGY_WINDOW = 84" in source
    assert "SHARPE7_WINDOW = 7" in source
