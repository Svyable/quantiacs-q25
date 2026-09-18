"""Mechanical tests for q25_deadline_hit126_consistency_v1."""
import numpy as np
import pandas as pd
import xarray as xr

from strategies.generated import q25_deadline_hit126_consistency as m


def panel(n=520, assets=8):
    rng = np.random.default_rng(2026091803)
    dates = pd.date_range("2015-01-01", periods=n, freq="D")
    drift = np.linspace(-0.0004, 0.0015, assets)
    ret = rng.normal(0, 0.018, (n, assets)) + drift[None, :]
    close = 100 * np.exp(np.cumsum(ret, axis=0))
    opened = np.vstack([close[:1], close[:-1]])
    high = np.maximum(opened, close) * 1.012
    low = np.minimum(opened, close) * 0.988
    vol = rng.lognormal(10, .5, (n, assets))
    liquid = np.ones((n, assets))
    liquid[350:370, -1] = 0
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
    assert float(w.min()) >= -1e-12
    assert float(w.max()) <= m.NAME_CAP + 1e-12
    assert float(w.sum("asset").max()) <= 1 + 1e-12
    liq = d.sel(field="is_liquid").transpose("time", "asset")
    assert float(w.where(liq <= 0, 0).sum()) == 0
    assert np.count_nonzero(w.values) > 0


def test_prefix_and_future_causality():
    d = panel()
    full = m.compute_weights(d)
    for cut in (250, 350, 430, 510):
        xr.testing.assert_allclose(
            m.strategy(d.isel(time=slice(0, cut + 1))),
            full.isel(time=cut, drop=True),
        )
    changed = d.copy(deep=True)
    changed.loc[dict(field="close", time=d.time[420:])] *= 4
    xr.testing.assert_allclose(
        full.isel(time=slice(0, 420)),
        m.compute_weights(changed).isel(time=slice(0, 420)),
    )


def test_asset_order_and_schedule():
    d = panel()
    base = m.compute_weights(d)
    rev = d.sel(asset=list(reversed(d.asset.values)))
    xr.testing.assert_allclose(base, m.compute_weights(rev).sel(asset=d.asset))

    w = base.to_pandas()
    changed = w.diff().abs().sum(axis=1) > 1e-10
    liquid = d.sel(field="is_liquid").transpose("time", "asset").to_pandas() > 0
    exits = ((~liquid) & liquid.shift(1, fill_value=False)).any(axis=1)
    mondays = pd.Series(w.index.dayofweek == 0, index=w.index)
    assert bool((changed & ~(mondays | exits)).sum() == 0)
