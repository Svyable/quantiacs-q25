"""Mechanism and lifecycle regressions; synthetic panels are never alpha evidence."""
import json
import numpy as np
import pandas as pd
import pytest
import xarray as xr
from research.benchmark import ROOT, check_causality, check_weights, load_module
from research.iteration import load_manifest
from test_frontier_c import panel

DIRECTORY = ROOT / 'experiments/frontier_20260910d'
FAMILIES = ('variance_ratio_reversal', 'rank_transition')


def module(family):
    return load_module(ROOT / f'strategies/generated/frontier_20260910d_{family}.py')


@pytest.mark.parametrize('family', FAMILIES)
@pytest.mark.parametrize('window', [42, 63, 84])
@pytest.mark.parametrize('mode', ['base', 'ablation', 'falsifier'])
def test_grid_causal_replay_and_asset_order(family, window, mode):
    data = panel()
    m = module(family)
    fn = lambda d: m.strategy(d, {'window': window, 'top_k': 5}, mode)
    weights = fn(data)
    check_weights(weights, data)
    assert check_causality(fn, data, weights)['status'] == 'PASS'
    reordered = data.sel(asset=data.asset.values[::-1])
    xr.testing.assert_allclose(fn(reordered).sel(asset=data.asset), weights)
    assert (weights.values > 0).any()


@pytest.mark.parametrize('family', FAMILIES)
def test_exit_does_not_revive_before_rebalance(family):
    m = module(family)
    times = pd.date_range('2020-01-06', periods=8)  # Monday through Monday
    score = pd.DataFrame(1., index=times, columns=['A', 'B'])
    liquid = score.astype(bool)
    liquid.iloc[1, 0] = False
    w = m._allocate(score, liquid, times, 5)
    assert w.sel(asset='A').values.tolist() == [.2, 0, 0, 0, 0, 0, 0, .2]
    assert np.all(w.sel(asset='B').values == .2)


@pytest.mark.parametrize('family', FAMILIES)
def test_future_listing_does_not_change_existing_path(family):
    d = panel()
    missing = xr.full_like(d.isel(asset=[0]), np.nan).assign_coords(asset=['FUTURE'])
    missing.loc[dict(field='is_liquid')] = 0.
    expanded = xr.concat([d, missing], dim='asset')
    m = module(family)
    for mode in ('base', 'ablation', 'falsifier'):
        xr.testing.assert_allclose(m.strategy(expanded, mode=mode).sel(asset=d.asset), m.strategy(d, mode=mode))
        assert float(m.strategy(expanded, mode=mode).sel(asset='FUTURE').max()) == 0.


def test_falsifier_preserves_eligible_marginal():
    m = module('rank_transition')
    values = pd.DataFrame([[.1, 99., .8, .3], [.2, 99., np.nan, .9]], columns=['D','X','A','B'])
    eligible = values.ne(99.) & values.notna()
    got = m._rotate_eligible(values, eligible)
    for i in range(len(values)):
        mask = eligible.iloc[i]
        assert sorted(got.iloc[i][mask]) == sorted(values.iloc[i][mask])
    assert np.all(got.X == 99.)
    assert not got.equals(values)
    pd.testing.assert_frame_equal(m._rotate_eligible(values[values.columns[::-1]], eligible).reindex(columns=values.columns), got)


def test_variance_ratio_distinguishes_serial_order():
    m = module('variance_ratio_reversal')
    data = panel(n=200, assets=3)
    # Equal one-day marginal distributions, different chronological order.
    alternating = np.tile([-.02, .022], 100)
    persistent = np.tile(np.repeat([-.02, .022], 5), 20)
    returns = np.column_stack([alternating, persistent, np.full(200, .001)])
    close = 100 * np.exp(np.cumsum(returns, axis=0))
    data.loc[dict(field='close')] = close
    data.loc[dict(field='is_liquid')] = 1.
    score, _ = m.signals(data, 42)
    falsifier, _ = m.signals(data, 42, 'falsifier')
    assert score.iloc[100:, 0].max() > 0
    assert falsifier.iloc[100:, 0].max() == 0
    assert falsifier.iloc[100:, 1].max() > 0


def test_campaign_contract():
    slate = json.loads((DIRECTORY / 'idea_slate.json').read_text())
    assert len(slate) == 24
    assert len({x['area'] for x in slate}) == 4
    assert all(sum(x['scores'].values()) == x['priority_score'] for x in slate)
    assert len(list(DIRECTORY.glob('*/preregistration.json'))) == 6
    manifest = load_manifest(DIRECTORY / 'manifest.json')
    assert len(manifest['candidates']) == 10
    assert manifest['automatic_promotion'] is False
