"""Causality, mechanics and evidence-boundary regression tests (no data key)."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
import xarray as xr
from research.benchmark import (ROOT, check_causality, check_weights, control_weights,
    load_module, panel_hash, residual_diagnostics, selection_score, validate_panel)
from research.campaign import CAMPAIGN, IMPLEMENTED
from research.iteration import family_decisions, load_manifest, rank_rows


def panel(n=500, assets=8):
    rng = np.random.default_rng(20260910)
    shocks = rng.normal(0, 0.025, (n, assets)) + 0.001
    close = 100 * np.exp(np.cumsum(shocks, axis=0))
    opened = np.vstack([close[:1], close[:-1]]) * np.exp(rng.normal(0, .005, (n, assets)))
    high = np.maximum(close, opened) * (1 + rng.uniform(.005, .04, (n, assets)))
    low = np.minimum(close, opened) * (1 - rng.uniform(.005, .04, (n, assets)))
    vol = rng.lognormal(10, .8, (n, assets))
    liquid = np.ones((n, assets))
    liquid[100:180, -1] = 0
    liquid[250:260, :] = 0
    fields = ['open', 'high', 'low', 'close', 'vol', 'is_liquid']
    return xr.DataArray(np.stack([opened, high, low, close, vol, liquid]),
        dims=('field', 'time', 'asset'), coords={'field': fields,
        'time': pd.date_range('2015-01-01', periods=n), 'asset': [f'A{i}' for i in range(assets)]}, name='cryptodaily')


def module(family):
    return load_module(ROOT / f'strategies/generated/{CAMPAIGN}_{family}.py')


@pytest.mark.parametrize('family', IMPLEMENTED)
@pytest.mark.parametrize('mode', ['base', 'ablation', 'falsifier'])
def test_causality_and_replay(family, mode):
    m, d = module(family), panel()
    fn = lambda x: m.strategy(x, mode=mode)
    w = fn(d)
    assert check_causality(fn, d, w)['status'] == 'PASS'
    xr.testing.assert_equal(w, fn(d))
    assert np.count_nonzero(w) > 0  # all-cash implementations cannot fake a pass
    assert float(w.isel(time=slice(250, 260)).sum()) == 0
    shuffled = d.sel(asset=list(reversed(d.asset.values)))
    xr.testing.assert_allclose(fn(shuffled).sel(asset=d.asset), w)


@pytest.mark.parametrize('family', IMPLEMENTED)
def test_grid_extremes_and_future_perturbation(family):
    m, d = module(family), panel()
    manifest = load_manifest(ROOT / f'experiments/{CAMPAIGN}/manifest.json')
    for c in manifest['candidates']:
        if c['family'] == family:
            fn = lambda x: m.strategy(x, c['params'], c['mode'])
            check_causality(fn, d, checkpoints=3)
    altered = d.copy(deep=True)
    altered.loc[dict(field='close', time=d.time[400:])] *= 9
    xr.testing.assert_equal(m.strategy(d).isel(time=slice(0, 400)),
                            m.strategy(altered).isel(time=slice(0, 400)))


@pytest.mark.parametrize('family', IMPLEMENTED)
def test_missing_data_single_asset_and_schedule(family):
    m, d = module(family), panel(200, 1)
    d.loc[dict(field='close', time=d.time[70:80])] = np.nan
    d.loc[dict(field='vol', time=d.time[20:40])] = 0
    d.loc[dict(field='is_liquid', time=d.time[90:95])] = np.nan
    w = m.strategy(d)
    check_weights(w, d)
    assert float(w.max()) <= .25
    assert float(w.isel(time=slice(90, 95)).sum()) == 0
    steady = panel(250)
    target = m.strategy(steady).to_pandas()
    changed = target.diff().abs().sum(axis=1) > 1e-10
    # The last asset is de-listed at day 100; that is an allowed off-cycle exit.
    assert all(t.dayofweek == 0 or t == steady.time.values[100] for t in target.index[changed])


@pytest.mark.parametrize('name', ['equal_liquid', 'inverse_vol_trend', 'persistent_low_vol'])
def test_controls(name):
    d = panel()
    assert check_causality(lambda x: control_weights(x, name), d)['status'] == 'PASS'


def metrics(value):
    return {fold: {cost: dict(sharpe_ratio=value, equity=1.1, max_drawdown=-.2, avg_turnover=.02)
                   for cost in ['0.00', '0.04', '0.08', '0.12']} for fold in ['research', 'dev']}


def test_rank_excludes_missing_failed_nan_and_ignores_future():
    base = metrics(1.2)
    base['validation'] = {'0.04': {'sharpe_ratio': 900}}
    assert selection_score(base) == 1.2
    rows = [dict(id='a', family='f', mode='base', status='COMPLETE', metrics=base),
            dict(id='b', family='f', mode='base', status='FAILED', metrics=metrics(900)),
            dict(id='c', family='f', mode='base', status='PENDING')]
    ranked = rank_rows(rows)
    assert ranked[0]['id'] == 'a' and ranked[0]['rank'] == 1
    assert all(r['rank'] is None for r in ranked[1:])
    base['dev']['0.12']['sharpe_ratio'] = None
    assert selection_score(base) is None
    base['dev']['0.12']['sharpe_ratio'] = float('nan')
    assert selection_score(base) is None


def test_falsifier_freezes_family_and_partial_grid_never_ranks():
    manifest = load_manifest(ROOT / f'experiments/{CAMPAIGN}/manifest.json')
    records = [dict(id=c['id'], family=c['family'], mode=c['mode'], status='COMPLETE',
                    metrics=metrics(1.0 if c['mode'] == 'base' else 1.1)) for c in manifest['candidates']]
    assert all(r['decision'] == 'FREEZE' for r in family_decisions(manifest, records))
    assert all(r['family_rank'] is None for r in family_decisions(manifest, records[:1]))


def test_panel_identity_coverage_and_arithmetic_label():
    d = panel(800)
    validate_panel(d, '2016-01-01', '2016-12-31')
    assert panel_hash(d) == panel_hash(d.sel(asset=d.asset.values[::-1]))
    with pytest.raises(ValueError):
        validate_panel(d.rename('wrong'), '2016-01-01', '2016-12-31')
    with pytest.raises(ValueError):
        validate_panel(d.isel(time=slice(0, 400)), '2016-01-01', '2016-12-31')
    with pytest.raises(ValueError):
        validate_panel(d.isel(time=list(range(400)) + list(range(401, 800))), '2016-01-01', '2016-12-31')


def test_real_leak_is_detected():
    d = panel()
    def leaking(x):
        w = control_weights(x, 'equal_liquid')
        return w * float(x.sel(field='close').isel(time=-1).mean() > 101)
    # Explicit future-mean path gives different earlier allocations by construction.
    def obvious(x):
        return control_weights(x, 'equal_liquid') * (x.sizes['time'] / 1000)
    with pytest.raises(ValueError, match='prefix causality'):
        check_causality(obvious, d)


def test_preregistrations_and_standalone_contract():
    directory = ROOT / f'experiments/{CAMPAIGN}'
    slate = json.loads((directory / 'idea_slate.json').read_text())
    assert len(slate) == 24 and len({s['area'] for s in slate}) == 4
    assert all(sum(s['scores'].values()) == s['priority_score'] for s in slate)
    assert len(list(directory.glob('*/preregistration.json'))) == 6
    manifest = load_manifest(directory / 'manifest.json')
    assert len(manifest['candidates']) == 15
    for family in IMPLEMENTED:
        source = (ROOT / f'strategies/generated/{CAMPAIGN}_{family}.py').read_text()
        assert 'from research' not in source and 'from factory' not in source
        assert 'PENDING RESEARCH STRATEGY' in source


def test_residual_fit_uses_earlier_fold_only():
    rng = np.random.default_rng(2)
    def series(n):
        return pd.Series(rng.normal(0, .01, n), index=pd.date_range('2016-01-01', periods=n))
    control = {'research': series(200), 'dev': series(200)}
    target = {k: v * .5 + .001 for k, v in control.items()}
    result = residual_diagnostics(target, {'control': control})
    assert result['status'] == 'LOCAL_CONTROL_DIAGNOSTIC_ONLY'
    assert result['correlations']['control'] == pytest.approx(1)


def test_benchmark_adapter_exact_cost_and_cleaner_contract():
    from research.benchmark import QuantiacsEvaluator
    d = panel(800)
    evaluator = object.__new__(QuantiacsEvaluator)
    evaluator.data = d
    calls = []
    class Output:
        @staticmethod
        def clean(w, data, kind):
            assert kind == 'crypto_daily_long'
            return w
    class Stats:
        @staticmethod
        def calc_stat(data, w, slippage_factor, points_per_year):
            calls.append((str(w.time.values[0])[:10], str(w.time.values[-1])[:10], slippage_factor))
            assert points_per_year == 365 and data.name == 'cryptodaily'
            assert pd.Timestamp(data.time.values.min()) < pd.Timestamp(w.time.values.min())
            fields = ['sharpe_ratio','mean_return','volatility','max_drawdown','equity','avg_turnover','relative_return']
            return xr.DataArray(np.zeros((w.sizes['time'], len(fields))), dims=('time','field'),
                coords={'time': w.time, 'field': fields})
    evaluator.output, evaluator.stats = Output, Stats
    folds = [dict(id='research', start='2016-01-01', end='2016-12-31')]
    result, returns = evaluator.evaluate(control_weights(d, 'equal_liquid'), folds, [0, .04, .08, .12])
    assert [c[2] for c in calls] == [0, .04, .08, .12]
    assert all(c[:2] == ('2016-01-01', '2016-12-31') for c in calls)
    assert len(returns['research']) == 366
    evaluator.output = type('BadOutput', (), {'clean': staticmethod(lambda w, d, k: w * .5)})
    with pytest.raises(AssertionError):
        evaluator.evaluate(control_weights(d, 'equal_liquid'), folds, [.04])


def test_blocked_run_contains_no_metrics_or_ranks(tmp_path, monkeypatch):
    import research.iteration as engine
    def unavailable():
        raise RuntimeError('public data unavailable')
    monkeypatch.setattr(engine, 'ensure_local_data_access', unavailable)
    path, complete = engine.run(ROOT / f'experiments/{CAMPAIGN}/manifest.json', tmp_path, 1)
    assert not complete
    status = json.loads((path / 'status.json').read_text())
    assert status['metrics'] is None
    assert status['quantiacs_access_mode'] == 'unknown'
    ranks = json.loads((path / 'rankings.json').read_text())
    assert all(c['rank'] is None for c in ranks['candidates'])


def test_iteration_budget_resume_and_preserved_failures(tmp_path, monkeypatch):
    import sys
    import types
    import research.iteration as engine
    d = panel(2922)
    fake_qnt = types.ModuleType('qnt')
    fake_data = types.ModuleType('qnt.data')
    fake_stats = types.ModuleType('qnt.stats')
    fake_stats.__file__ = __file__
    fake_data.cryptodaily_load_data = lambda **kwargs: d
    fake_qnt.data, fake_qnt.stats = fake_data, fake_stats
    monkeypatch.setitem(sys.modules, 'qnt', fake_qnt)
    monkeypatch.setitem(sys.modules, 'qnt.data', fake_data)
    monkeypatch.setitem(sys.modules, 'qnt.stats', fake_stats)
    monkeypatch.setattr(engine, 'ensure_local_data_access', lambda: 'default')
    monkeypatch.setattr(engine, 'quantiacs_access_mode', lambda: 'public_default')
    monkeypatch.setattr(engine, 'check_causality', lambda *a: {'status': 'TEST_DOUBLE'})
    calls = []
    class Evaluator:
        def __init__(self, data):
            pass
        def evaluate(self, weights, folds, costs):
            calls.append(1)
            if len(calls) == 1:
                raise ValueError('deliberate test failure')
            rr = {f['id']: pd.Series(0., index=pd.date_range(f['start'], f['end'])) for f in folds}
            return metrics(0.0), rr
    monkeypatch.setattr(engine, 'QuantiacsEvaluator', Evaluator)
    manifest = ROOT / f'experiments/{CAMPAIGN}/manifest.json'
    first, _ = engine.run(manifest, tmp_path, 1)
    failure = (first / 'equal_liquid.json').read_bytes()
    second, _ = engine.run(manifest, tmp_path, 1)
    assert first == second and len(calls) == 2
    assert (first / 'equal_liquid.json').read_bytes() == failure
    attempts = (first / 'attempts.jsonl').read_text().splitlines()
    assert len(attempts) == 2
    assert json.loads(attempts[0])['id'] != json.loads(attempts[1])['id']
