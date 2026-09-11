"""Verify distinct structures, delayed learning labels and bounded policy state."""
import json
import numpy as np
import pandas as pd
import pytest
import xarray as xr
from research.benchmark import ROOT, check_causality, load_module
from research.iteration import load_manifest
from test_frontier_c import panel
CAMPAIGN='frontier_20260911f'
FAMILIES=('triangle_coherence','weekly_payoff_posterior','adaptive_expert_cash')


def test_observed_evidence_matches_frozen_implementation_and_classification():
    from research.preregister import sha256_file
    dest=ROOT/'experiments'/CAMPAIGN
    evidence=ROOT/'evidence'/CAMPAIGN
    freeze=json.loads((dest/'implementation_freeze.json').read_text())
    assert all(sha256_file(ROOT/path)==h for path,h in freeze['sha256'].items())
    manifest=load_manifest(dest/'manifest.json')
    context=json.loads((evidence/'context.json').read_text())
    assert context['manifest_sha256']==sha256_file(dest/'manifest.json')
    for job in manifest['candidates']:
        row=json.loads((evidence/'candidate_packets'/(job['id']+'.json')).read_text())
        assert row['data_sha256']==context['data_sha256']
        assert row['strategy_source_sha256']==sha256_file(ROOT/job['path'])
        assert row['preregistration_sha256']==job['preregistration_sha256']
        assert row['params']==job['params']
        expected='allocator_experiment' if job['family']=='adaptive_expert_cash' else 'discovery_hypothesis'
        assert row['classification']==expected
    matrix=json.loads((evidence/'matrix.json').read_text())
    assert len(matrix['candidates'])==18
    assert all(row['status']=='COMPLETE' for row in matrix['candidates'])
    assert all(row['decision']=='FREEZE' for row in matrix['families'])


def module(family):
    return load_module(ROOT/f'strategies/generated/{CAMPAIGN}_{family}.py')


@pytest.mark.parametrize('family',FAMILIES)
@pytest.mark.parametrize('mode',('base','ablation','falsifier'))
@pytest.mark.parametrize('grid_index',(0,1,2))
def test_grid_causality_replay_and_order(family,mode,grid_index):
    window=([42,63,84] if family=='triangle_coherence' else [84,126,168])[grid_index]
    d=panel(n=720)
    fn=lambda data:module(family).strategy(data,{'window':window,'top_k':5},mode)
    weights=fn(d)
    assert check_causality(fn,d,weights)['status']=='PASS'
    assert (weights.values>0).any()
    xr.testing.assert_allclose(fn(d.sel(asset=d.asset.values[::-1])).sel(asset=d.asset),weights)


@pytest.mark.parametrize('family',FAMILIES)
def test_controls_change_holdings(family):
    d=panel(n=720);m=module(family);base=m.strategy(d)
    for mode in ('ablation','falsifier'):
        assert float(abs(base-m.strategy(d,mode=mode)).sum())>.001


@pytest.mark.parametrize('family',FAMILIES)
@pytest.mark.parametrize('mode',('base','falsifier'))
def test_future_asset_cannot_change_active_history(family,mode):
    d=panel(n=720)
    absent=xr.full_like(d.isel(asset=[0]),np.nan).assign_coords(asset=['FUTURE'])
    absent.loc[dict(field='is_liquid')]=0
    expanded=xr.concat([d,absent],dim='asset');m=module(family)
    xr.testing.assert_allclose(m.strategy(expanded,mode=mode).sel(asset=d.asset),m.strategy(d,mode=mode))


def test_triangle_balance_distinguishes_signed_motifs():
    m=module('triangle_coherence')
    positive=np.array([[1,.3,.3],[.3,1,.3],[.3,.3,1]])
    np.testing.assert_allclose(m._balance(positive),1)
    positive[0,1]=positive[1,0]=-.3
    np.testing.assert_allclose(m._balance(positive),-1)
    assert np.isnan(m._balance(np.eye(3))).all()


def test_weekly_labels_are_fully_realized_nonoverlapping():
    m=module('weekly_payoff_posterior')
    dates=pd.date_range('2020-01-06',periods=29)
    close=pd.DataFrame({'A':np.exp(np.arange(29)*.01)},index=dates)
    liquid=close.notna();state=pd.Series(True,index=dates)
    labels=m._weekly_labels(close,liquid,state).A.dropna()
    assert list(labels.index)==list(dates[[7,14,21,28]])
    np.testing.assert_allclose(labels,.07)
    altered=close.copy();altered.iloc[14:]*=2
    pd.testing.assert_frame_equal(m._weekly_labels(altered,liquid,state).iloc[:14],m._weekly_labels(close,liquid,state).iloc[:14])


def test_probability_payoff_arithmetic_has_declared_priors():
    m=module('weekly_payoff_posterior')
    labels=pd.DataFrame({'A':[.1,.1,-.05,-.05]})
    score,n=m._posterior(labels,pd.Series(True,index=labels.index),4)
    assert n.A.iloc[-1]==4
    assert score.A.iloc[-1]==pytest.approx(1/17)


def test_policy_uses_previous_utilities_and_can_prefer_cash():
    m=module('adaptive_expert_cash')
    proxy=pd.DataFrame({'trend':[-.01]*150,'defensive':[-.005]*150})
    p=m._expert_probabilities(proxy,84,'base')
    assert p.cash.iloc[-1]>p.defensive.iloc[-1]>p.trend.iloc[-1]
    np.testing.assert_allclose(p.iloc[-1].sum(),1.)
    changed=proxy.copy();changed.iloc[-1]=1
    pd.testing.assert_series_equal(m._expert_probabilities(changed,84,'base').iloc[-1],p.iloc[-1])
    inverse=m._expert_probabilities(proxy,84,'falsifier')
    assert inverse.trend.iloc[-1]==pytest.approx(p.defensive.iloc[-1])
    assert inverse.cash.iloc[-1]==pytest.approx(p.cash.iloc[-1])


def test_campaign_classifies_allocator_honestly():
    dest=ROOT/'experiments'/CAMPAIGN
    manifest=load_manifest(dest/'manifest.json')
    assert len(manifest['candidates'])==15
    assert len(list(dest.glob('*/preregistration.json')))==6
    slate=json.loads((dest/'idea_slate.json').read_text())
    assert len(slate)==24 and len({x['area'] for x in slate})==4
    spec=json.loads((dest/'adaptive_expert_cash/preregistration.json').read_text())
    assert spec['classification']=='allocator_experiment'
    assert spec['novelty_axes_changed']==['transform']
