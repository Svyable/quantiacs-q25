import numpy as np
import xarray as xr
from strategies.generated.q25_vcb_breadth_turnover_ensemble import apply_no_trade_band


def _target(values, assets=("a", "b")):
    return xr.DataArray(np.asarray(values, dtype=float), dims=("time", "asset"), coords={"time": np.arange(len(values)), "asset": list(assets)})


def test_band_retains_prior_weight_below_two_points_and_moves_at_boundary():
    t = _target([[.10, .20], [.119, .181], [.12, .18], [.141, .159]])
    w = apply_no_trade_band(t)
    np.testing.assert_allclose(w.values[0], [.10, .20])
    np.testing.assert_allclose(w.values[1], [.10, .20])
    np.testing.assert_allclose(w.values[2], [.10, .18])
    np.testing.assert_allclose(w.values[3], [.141, .159])


def test_band_is_long_only_gross_bounded_and_asset_order_invariant():
    t = _target([[.8, .6], [-.1, .3], [.2, .31]])
    w = apply_no_trade_band(t)
    assert float(w.min()) >= 0
    assert bool((w.sum("asset") <= 1.0 + 1e-12).all())
    rev = apply_no_trade_band(t.sel(asset=["b", "a"])).sel(asset=["a", "b"])
    xr.testing.assert_allclose(w, rev)


def test_band_is_prefix_invariant():
    t = _target([[.1, .2], [.11, .21], [.3, .1], [.29, .11], [.5, .2]])
    full = apply_no_trade_band(t)
    prefix = apply_no_trade_band(t.isel(time=slice(0, 4)))
    xr.testing.assert_allclose(full.isel(time=slice(0, 4)), prefix)


def test_band_is_deterministic():
    t = _target([[.1, .2], [.13, .19], [.14, .4]])
    xr.testing.assert_identical(apply_no_trade_band(t), apply_no_trade_band(t))
