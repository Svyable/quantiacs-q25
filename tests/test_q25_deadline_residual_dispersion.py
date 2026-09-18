"""Mechanical tests for q25_deadline_residual_dispersion_v1."""
import numpy as np
import pandas as pd
import xarray as xr

from strategies.generated import q25_deadline_residual_dispersion as m


def panel(n=700, assets=8):
    rng = np.random.default_rng(2026091802)
    dates = pd.date_range("2014-12-01", periods=n, freq="D")
    market = rng.normal(0.0004, 0.015, n)
    beta = np.linspace(0.6, 1.4, assets)
    idio_scale = np.where(np.arange(n)[:, None] % 160 < 80, 0.008, 0.025)
    drift = np.linspace(-0.0003, 0.0010, assets)[None, :]
    ret = market[:, None] * beta[None, :] + rng.normal(0, 1, (n, assets)) * idio_scale + drift
    close = 100.0 * np.exp(np.cumsum(ret, axis=0))
    opened = np.vstack([close[:1], close[:-1]])
    high = np.maximum(opened, close) * 1.01
    low = np.minimum(opened, close) * 0.99
    vol = rng.lognormal(10.0, 0.5, (n, assets))
    liquid = np.ones((n, assets))
    liquid[480:500, -1] = 0.0
    fields = ["open", "high", "low", "close", "vol", "is_liquid"]
    return xr.DataArray(
        np.stack([opened, high, low, close, vol, liquid]),
        dims=("field", "time", "asset"),
        coords={"field": fields, "time": dates, "asset": [f"A{i}" for i in range(assets)]},
        name="cryptodaily",
    )


def test_mechanics():
    d = panel()
    w = m.compute_weights(d)
    assert w.dims == ("time", "asset")
    assert float(w.min()) >= -1e-12
    assert float(w.max()) <= m.NAME_CAP + 1e-12
    assert float(w.sum("asset").max()) <= 1.0 + 1e-12
    liquid = d.sel(field="is_liquid").transpose("time", "asset")
    assert float(w.where(liquid <= 0.0, 0.0).sum()) == 0.0
    assert np.count_nonzero(w.values) > 0


def test_prefix_invariance():
    d = panel()
    full = m.compute_weights(d)
    for cut in (420, 500, 610, 690):
        latest = m.strategy(d.isel(time=slice(0, cut + 1)))
        xr.testing.assert_allclose(latest, full.isel(time=cut, drop=True))


def test_future_perturbation():
    d = panel()
    a = m.compute_weights(d)
    altered = d.copy(deep=True)
    altered.loc[dict(field="close", time=d.time[570:])] *= 5.0
    b = m.compute_weights(altered)
    xr.testing.assert_allclose(a.isel(time=slice(0, 570)), b.isel(time=slice(0, 570)))


def test_asset_order_invariance():
    d = panel()
    base = m.compute_weights(d)
    rev = d.sel(asset=list(reversed(d.asset.values)))
    xr.testing.assert_allclose(base, m.compute_weights(rev).sel(asset=d.asset))


def test_schedule_or_liquidity_exit_only():
    d = panel()
    w = m.compute_weights(d).to_pandas()
    changed = w.diff().abs().sum(axis=1) > 1e-10
    liquid = d.sel(field="is_liquid").transpose("time", "asset").to_pandas() > 0
    exits = ((~liquid) & liquid.shift(1, fill_value=False)).any(axis=1)
    mondays = pd.Series(w.index.dayofweek == 0, index=w.index)
    assert bool((changed & ~(mondays | exits)).sum() == 0)
