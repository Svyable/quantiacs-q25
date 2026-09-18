"""Mechanical tests for q25_deadline_cocrash_shelter_v1."""
import numpy as np
import pandas as pd
import xarray as xr

from strategies.generated import q25_deadline_cocrash_shelter as m


def panel(n=620, assets=8):
    rng = np.random.default_rng(20260918)
    dates = pd.date_range("2015-01-01", periods=n, freq="D")
    market = rng.normal(0.0005, 0.018, n)
    loadings = np.linspace(0.25, 1.35, assets)
    idio = rng.normal(0.0, 0.012, (n, assets))
    returns = market[:, None] * loadings[None, :] + idio
    close = 100.0 * np.exp(np.cumsum(returns, axis=0))
    opened = np.vstack([close[:1], close[:-1]])
    high = np.maximum(opened, close) * 1.015
    low = np.minimum(opened, close) * 0.985
    vol = rng.lognormal(10.0, 0.4, (n, assets))
    liquid = np.ones((n, assets))
    liquid[430:455, -1] = 0.0
    fields = ["open", "high", "low", "close", "vol", "is_liquid"]
    return xr.DataArray(
        np.stack([opened, high, low, close, vol, liquid]),
        dims=("field", "time", "asset"),
        coords={"field": fields, "time": dates, "asset": [f"A{i}" for i in range(assets)]},
        name="cryptodaily",
    )


def test_long_liquid_capped_and_bounded_gross():
    d = panel()
    w = m.compute_weights(d)
    assert w.dims == ("time", "asset")
    assert float(w.min()) >= -1e-12
    assert float(w.max()) <= m.NAME_CAP + 1e-12
    assert float(w.sum("asset").max()) <= 1.0 + 1e-12
    liquid = d.sel(field="is_liquid").transpose("time", "asset")
    assert float(w.where(liquid <= 0.0, 0.0).sum()) == 0.0
    assert np.count_nonzero(w.values) > 0


def test_prefix_invariance_matches_single_to_multipass_semantics():
    d = panel()
    full = m.compute_weights(d)
    for cut in (360, 430, 510, 600):
        prefix = d.isel(time=slice(0, cut + 1))
        latest = m.strategy(prefix)
        xr.testing.assert_allclose(latest, full.isel(time=cut, drop=True))


def test_future_price_perturbation_cannot_change_past_weights():
    d = panel()
    base = m.compute_weights(d)
    altered = d.copy(deep=True)
    altered.loc[dict(field="close", time=d.time[500:])] *= 7.0
    changed = m.compute_weights(altered)
    xr.testing.assert_allclose(
        base.isel(time=slice(0, 500)),
        changed.isel(time=slice(0, 500)),
    )


def test_asset_order_invariance():
    d = panel()
    base = m.compute_weights(d)
    rev = d.sel(asset=list(reversed(d.asset.values)))
    got = m.compute_weights(rev).sel(asset=d.asset)
    xr.testing.assert_allclose(base, got)


def test_position_changes_are_weekly_or_for_liquidity_exit():
    d = panel()
    w = m.compute_weights(d).to_pandas()
    changed = w.diff().abs().sum(axis=1) > 1e-10
    liquid = d.sel(field="is_liquid").transpose("time", "asset").to_pandas() > 0
    exited = ((~liquid) & liquid.shift(1, fill_value=False)).any(axis=1)
    allowed = pd.Series(w.index.dayofweek == 0, index=w.index) | exited
    assert bool((~allowed & changed).sum() == 0)
