import numpy as np
import xarray as xr

from strategies.generated.q25_vcb_breadth_sparse_trigger_ensemble import apply_sparse_trigger


def panel(values, assets=("a", "b")):
    values=np.asarray(values,float)
    return xr.DataArray(values,coords={"time":np.arange(values.shape[0]),"asset":list(assets)},dims=("time","asset"))


def test_threshold_boundary_and_accumulation():
    target=panel([[.04,.04],[.049,.049],[.051,.051],[.08,.08]])
    eligible=panel(np.ones((4,2)))
    got=apply_sparse_trigger(target,eligible)
    # Initial displacement .04 < .05: stay flat. Next .049 < .05: still flat.
    np.testing.assert_allclose(got.values[:2],0)
    # .051 one-way displacement exceeds threshold, so the whole target executes.
    np.testing.assert_allclose(got.values[2],[.051,.051])
    # Subsequent displacement .029 < threshold: retain prior holdings.
    np.testing.assert_allclose(got.values[3],[.051,.051])


def test_liquidity_exit_is_mandatory_below_trigger():
    target=panel([[.20,.20],[.20,.20]])
    eligible=panel([[1,1],[0,1]])
    got=apply_sparse_trigger(target,eligible)
    np.testing.assert_allclose(got.values[0],[.20,.20])
    np.testing.assert_allclose(got.values[1],[0,.20])


def test_long_only_gross_and_asset_order_invariance():
    target=panel([[.8,.8],[-.2,.3],[.1,.1]])
    eligible=panel(np.ones((3,2)))
    got=apply_sparse_trigger(target,eligible)
    assert float(got.min()) >= 0
    assert float(got.sum("asset").max()) <= 1 + 1e-12
    rev=apply_sparse_trigger(target.sel(asset=["b","a"]),eligible.sel(asset=["b","a"])).sel(asset=["a","b"])
    np.testing.assert_allclose(got.values,rev.values)


def test_prefix_invariance_and_determinism():
    target=panel([[.2,.1],[.22,.11],[.4,.1],[.39,.11],[.1,.2]])
    eligible=panel(np.ones((5,2)))
    full=apply_sparse_trigger(target,eligible)
    prefix=apply_sparse_trigger(target.isel(time=slice(0,4)),eligible.isel(time=slice(0,4)))
    np.testing.assert_allclose(full.isel(time=slice(0,4)).values,prefix.values)
    np.testing.assert_allclose(full.values,apply_sparse_trigger(target,eligible).values)
