import importlib
import numpy as np
import xarray as xr

M = importlib.import_module("strategies.generated.q25_volatility_contraction_breakout")


def _fixture(seed=122, days=260, assets=10):
    rng = np.random.default_rng(seed)
    t = np.arange(np.datetime64("2024-01-01"), np.datetime64("2024-01-01") + days)
    a = np.array([f"A{i}" for i in range(assets)])
    r = rng.normal(0.0007, 0.022, (days, assets))
    # Deterministic quiet-to-breakout path without naming any contest asset.
    r[90:145, 0] *= 0.25
    r[145:170, 0] += 0.006
    close = 100 * np.exp(np.cumsum(r, axis=0))
    liquid = np.ones_like(close)
    liquid[-20:, 3] = 0
    return xr.DataArray(np.stack([close, liquid]), dims=("field", "time", "asset"), coords={"field": ["close", "is_liquid"], "time": t, "asset": a})


def test_vcb_exact_bounded_replay_and_determinism():
    data = _fixture()
    full = M.calculate_weights(data)
    rerun = M.calculate_weights(data)
    xr.testing.assert_allclose(full, rerun, rtol=0, atol=0)
    for cut in (150, 190, 230):
        bounded = M.calculate_weights(data.isel(time=slice(0, cut)))
        xr.testing.assert_allclose(full.isel(time=slice(0, cut)), bounded, rtol=0, atol=1e-12)


def test_vcb_single_vs_incremental_multipass_last_row_parity():
    data = _fixture()
    full = M.calculate_weights(data)
    # Recompute every decision from its available prefix; this is deliberately
    # expensive only on a sparse set of checkpoints and proves state-free parity.
    for cut in range(150, data.sizes["time"] + 1, 11):
        one = M.calculate_weights(data.isel(time=slice(0, cut))).isel(time=-1)
        xr.testing.assert_allclose(full.isel(time=cut - 1), one, rtol=0, atol=1e-12)


def test_vcb_constraints_survive_liquidity_exit():
    data = _fixture()
    w = M.calculate_weights(data)
    assert float(w.min()) >= -1e-15
    assert float(w.max()) <= 0.25 + 1e-12
    assert float(w.sum("asset").max()) <= 1.0 + 1e-12
    assert float(abs(w.sel(asset="A3", time=data.time[-20:])).max()) == 0.0
