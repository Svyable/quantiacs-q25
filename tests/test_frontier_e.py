"""Synthetic mechanics and frozen-contract checks, not return evidence."""
import json
import numpy as np
import pandas as pd
import pytest
import xarray as xr
from research.benchmark import ROOT, check_causality, load_module
from research.iteration import load_manifest
from test_frontier_c import panel

FAMILIES = ('downside_impact_relief', 'range_acceptance_escape', 'upside_response_convexity')
CAMPAIGN = 'frontier_20260911e'


def module(family):
    return load_module(ROOT/f'strategies/generated/{CAMPAIGN}_{family}.py')


@pytest.mark.parametrize('family', FAMILIES)
@pytest.mark.parametrize('mode', ('base', 'ablation', 'falsifier'))
@pytest.mark.parametrize('window', (42,63,84))
def test_full_grid_causality_replay_and_column_invariance(family, mode, window):
    data = panel(n=620)
    m = module(family)
    fn = lambda d: m.strategy(d, {'window':window, 'top_k':5}, mode)
    weights = fn(data)
    assert check_causality(fn, data, weights)['status'] == 'PASS'
    assert (weights.values > 0).any()
    xr.testing.assert_allclose(fn(data.sel(asset=data.asset.values[::-1])).sel(asset=data.asset), weights)


@pytest.mark.parametrize('family', FAMILIES)
def test_confidence_changes_capital_and_exit_persists(family):
    m = module(family)
    times = pd.date_range('2020-01-06', periods=8)
    score = pd.DataFrame(.5, index=times, columns=['A','B'])
    liquid = score.astype(bool)
    liquid.iloc[1,0] = False
    actual = m._allocate(score, liquid, times, 5)
    np.testing.assert_allclose(actual.sel(asset='A'), [.1,0,0,0,0,0,0,.1])
    stronger = m._allocate(score*2, liquid, times, 5)
    xr.testing.assert_allclose(stronger, actual*2)


@pytest.mark.parametrize('family', FAMILIES)
def test_ablation_and_falsifier_change_deployed_weights(family):
    d=panel(n=620);m=module(family);base=m.strategy(d)
    for mode in ('ablation','falsifier'):
        assert float(abs(base-m.strategy(d, mode=mode)).sum()) > .01


@pytest.mark.parametrize('family', FAMILIES)
@pytest.mark.parametrize('mode', ('base','falsifier'))
def test_inactive_future_assets_do_not_affect_existing_targets(family, mode):
    d=panel(n=620)
    future=xr.full_like(d.isel(asset=[0]),np.nan).assign_coords(asset=['FUTURE'])
    future.loc[dict(field='is_liquid')]=0
    expanded=xr.concat([d,future],dim='asset')
    m=module(family)
    xr.testing.assert_allclose(m.strategy(expanded,mode=mode).sel(asset=d.asset), m.strategy(d,mode=mode))


def test_peer_market_excludes_own_return():
    m=module('upside_response_convexity')
    r=pd.DataFrame([[.01,.02,.03,.99]],columns=list('ABCD'))
    mask=pd.DataFrame([[True,True,True,False]],columns=r.columns)
    peer=m._peer_market(r,mask)
    assert peer.A.iloc[0] == pytest.approx(.025)
    r.A=10.
    assert m._peer_market(r,mask).A.iloc[0] == pytest.approx(.025)
    assert peer.D.iloc[0] == pytest.approx(.02)


def test_response_distinguishes_convex_from_linear_exposure():
    m=module('upside_response_convexity')
    x=np.tile([.005,.01,.02,.04,-.02,-.01],30)
    peer=pd.DataFrame({'A':x,'B':x})
    returns=pd.DataFrame({'A':x+20*np.maximum(x,0)**2, 'B':1.5*x})
    tail=m._response(returns,peer,peer>.02,63)
    middle=m._response(returns,peer,(peer>0)&(peer<=.02),63)
    assert (tail.A-middle.A).iloc[-1] > .2
    assert (tail.B-middle.B).iloc[-1] == pytest.approx(0,abs=1e-12)


def test_registered_campaign_is_finite_and_unpromoted():
    dest=ROOT/'experiments'/CAMPAIGN
    manifest=load_manifest(dest/'manifest.json')
    assert len(manifest['candidates']) == 15
    assert len(list(dest.glob('*/preregistration.json'))) == 6
    slate=json.loads((dest/'idea_slate.json').read_text())
    assert len(slate) == 24
    assert len({x['area'] for x in slate}) == 4
    assert all(sum(x['scores'].values()) == x['priority_score'] for x in slate)
    assert not manifest['automatic_promotion']
