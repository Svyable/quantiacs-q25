import numpy as np

from research.fast_screen import (
    ScreenThresholds,
    annualized_sharpe,
    archive_correlations,
    evaluate_candidate,
    max_drawdown,
    pareto_mask,
    residual_sharpe,
)


def test_archive_correlations_recovers_identity_and_inverse():
    rng = np.random.default_rng(7)
    x = rng.normal(0.001, 0.02, size=400)
    archive = np.column_stack([x, -x, rng.normal(size=400)])
    c = archive_correlations(x, archive)
    assert c[0] > 0.999999
    assert c[1] < -0.999999
    assert abs(c[2]) < 0.15


def test_basic_metrics_are_sane():
    r = np.array([0.01, -0.005, 0.007, -0.002, 0.004] * 100)
    assert annualized_sharpe(r) > 0
    assert -1.0 < max_drawdown(r) <= 0.0


def test_residual_sharpe_removes_linear_core_exposure():
    rng = np.random.default_rng(9)
    core = rng.normal(0.001, 0.02, size=600)
    alpha = rng.normal(0.0008, 0.01, size=600)
    candidate = 0.8 * core + alpha
    rs = residual_sharpe(candidate, core)
    assert np.isfinite(rs)
    assert rs > 0


def test_evaluate_candidate_can_pass_relaxed_gate():
    rng = np.random.default_rng(11)
    n = 900
    r = rng.normal(0.0015, 0.01, size=n)
    stressed = r - 0.00005
    delayed = r * 0.9
    folds = [r[:300], r[300:600], r[600:]]
    pre = np.arange(n) < 600
    recent = ~pre
    archive_pre = rng.normal(size=(pre.sum(), 8))
    archive_recent = rng.normal(size=(recent.sum(), 8))
    t = ScreenThresholds(
        full_sharpe_min=-10,
        stressed_sharpe_min=-10,
        worst_fold_sharpe_min=-10,
        max_drawdown_abs_max=1.0,
        archive_corr_pre_max=1.0,
        archive_corr_recent_max=1.0,
        delay_retention_min=-10,
    )
    out = evaluate_candidate(
        r, stressed, folds, delayed, archive_pre, archive_recent, pre, recent, t
    )
    assert out.passed
    assert not out.failures


def test_pareto_mask():
    values = np.array([
        [2.0, 0.2],
        [1.5, 0.5],
        [1.0, 0.1],
        [2.0, 0.1],
    ])
    keep = pareto_mask(values, maximize=[True, True])
    assert keep.tolist() == [True, True, False, False]
