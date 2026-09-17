"""Fast, deterministic screening primitives for deadline-scale Q25 research.

This module intentionally avoids Quantiacs/xarray strategy execution. It accepts
already-computed daily candidate returns and frozen incumbent return matrices,
then applies cheap metrics/correlation gates before a candidate earns exact replay.

Fast screening is triage only. Finalists still require the exact strategy, full
cost accounting, causality/prefix checks, multipass, and hosted uniqueness checks.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Sequence

import numpy as np

TRADING_DAYS = 365.25


def _as_1d(x: Sequence[float]) -> np.ndarray:
    return np.asarray(x, dtype=np.float64).reshape(-1)


def _finite(x: np.ndarray) -> np.ndarray:
    return x[np.isfinite(x)]


def annualized_sharpe(r: Sequence[float], annualization: float = TRADING_DAYS) -> float:
    x = _finite(_as_1d(r))
    if x.size < 2:
        return float("nan")
    sd = x.std(ddof=1)
    if not np.isfinite(sd) or sd <= 0:
        return float("nan")
    return float(np.sqrt(annualization) * x.mean() / sd)


def max_drawdown(r: Sequence[float]) -> float:
    x = np.nan_to_num(_as_1d(r), nan=0.0, posinf=0.0, neginf=0.0)
    if x.size == 0:
        return float("nan")
    wealth = np.cumprod(1.0 + x)
    peaks = np.maximum.accumulate(wealth)
    dd = wealth / np.where(peaks > 0, peaks, np.nan) - 1.0
    return float(np.nanmin(dd))


def archive_correlations(candidate_returns: Sequence[float], archive_returns: np.ndarray) -> np.ndarray:
    """Pairwise-complete candidate-vs-archive correlations.

    ``archive_returns`` has shape ``(time, strategies)``. Each archive column is
    correlated using only dates on which both candidate and that column are finite.
    The implementation is vectorized over strategies, so this remains cheap for a
    large frozen archive while avoiding bias from mismatched NaN masks.
    """
    c = _as_1d(candidate_returns)
    a = np.asarray(archive_returns, dtype=np.float64)
    if a.ndim != 2 or a.shape[0] != c.size:
        raise ValueError("archive_returns must have shape (len(candidate_returns), n_strategies)")

    cf = np.isfinite(c)
    af = np.isfinite(a)
    mask = af & cf[:, None]
    n = mask.sum(axis=0).astype(np.float64)

    c0 = np.where(cf, c, 0.0)
    a0 = np.where(af, a, 0.0)
    m = mask.astype(np.float64)

    sx = c0 @ m
    sy = (a0 * cf[:, None]).sum(axis=0)
    sxx = (c0 * c0) @ m
    syy = ((a0 * a0) * cf[:, None]).sum(axis=0)
    sxy = c0 @ a0

    valid = n >= 2
    cov = np.full(a.shape[1], np.nan, dtype=np.float64)
    varx = np.full_like(cov, np.nan)
    vary = np.full_like(cov, np.nan)
    cov[valid] = sxy[valid] - sx[valid] * sy[valid] / n[valid]
    varx[valid] = sxx[valid] - sx[valid] * sx[valid] / n[valid]
    vary[valid] = syy[valid] - sy[valid] * sy[valid] / n[valid]
    denom = np.sqrt(np.maximum(varx, 0.0) * np.maximum(vary, 0.0))
    out = np.full_like(cov, np.nan)
    good = valid & np.isfinite(denom) & (denom > 0)
    out[good] = cov[good] / denom[good]
    return np.clip(out, -1.0, 1.0)


def max_abs_archive_corr(candidate_returns: Sequence[float], archive_returns: np.ndarray) -> float:
    corrs = archive_correlations(candidate_returns, archive_returns)
    if not np.isfinite(corrs).any():
        return float("nan")
    return float(np.nanmax(np.abs(corrs)))


def residual_sharpe(candidate_returns: Sequence[float], core_returns: np.ndarray) -> float:
    """Annualized factor-adjusted alpha divided by residual volatility.

    A plain OLS residual has zero sample mean when an intercept is fitted, so its
    Sharpe is mechanically ~0. We instead fit ``y = alpha + X beta + epsilon``
    and return the Sharpe of ``alpha + epsilon``. This preserves estimated alpha
    while removing contemporaneous linear core exposure.
    """
    y = _as_1d(candidate_returns)
    x = np.asarray(core_returns, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    if x.shape[0] != y.size:
        raise ValueError("core_returns must align with candidate_returns")
    mask = np.isfinite(y) & np.isfinite(x).all(axis=1)
    if mask.sum() <= x.shape[1] + 2:
        return float("nan")
    yy = y[mask]
    xx = np.column_stack([np.ones(mask.sum()), x[mask]])
    beta, *_ = np.linalg.lstsq(xx, yy, rcond=None)
    alpha = float(beta[0])
    resid = yy - xx @ beta
    adjusted = resid + alpha
    return annualized_sharpe(adjusted)


@dataclass(frozen=True)
class ScreenThresholds:
    full_sharpe_min: float = 1.15
    stressed_sharpe_min: float = 0.70
    worst_fold_sharpe_min: float = 0.20
    max_drawdown_abs_max: float = 0.50
    archive_corr_pre_max: float = 0.45
    archive_corr_recent_max: float = 0.50
    delay_retention_min: float = 0.70


@dataclass(frozen=True)
class ScreenResult:
    full_sharpe: float
    stressed_sharpe: float
    worst_fold_sharpe: float
    max_drawdown: float
    archive_corr_pre: float
    archive_corr_recent: float
    delayed_sharpe: float
    delay_retention: float
    passed: bool
    failures: tuple[str, ...]

    def as_dict(self) -> dict:
        return asdict(self)


def evaluate_candidate(
    returns: Sequence[float],
    stressed_returns: Sequence[float],
    fold_returns: Iterable[Sequence[float]],
    delayed_returns: Sequence[float],
    archive_pre: np.ndarray,
    archive_recent: np.ndarray,
    pre_mask: Sequence[bool],
    recent_mask: Sequence[bool],
    thresholds: ScreenThresholds = ScreenThresholds(),
) -> ScreenResult:
    r = _as_1d(returns)
    sr = annualized_sharpe(r)
    stress_sr = annualized_sharpe(stressed_returns)
    folds = [annualized_sharpe(x) for x in fold_returns]
    worst_fold = float(np.nanmin(folds)) if folds else float("nan")
    mdd = max_drawdown(r)

    pm = np.asarray(pre_mask, dtype=bool)
    rm = np.asarray(recent_mask, dtype=bool)
    if pm.size != r.size or rm.size != r.size:
        raise ValueError("pre_mask/recent_mask must align with returns")
    pre_corr = max_abs_archive_corr(r[pm], np.asarray(archive_pre, dtype=np.float64))
    recent_corr = max_abs_archive_corr(r[rm], np.asarray(archive_recent, dtype=np.float64))

    delayed_sr = annualized_sharpe(delayed_returns)
    retention = delayed_sr / sr if np.isfinite(sr) and sr > 0 else float("nan")

    checks = [
        (np.isfinite(sr) and sr >= thresholds.full_sharpe_min, "full_sharpe"),
        (np.isfinite(stress_sr) and stress_sr >= thresholds.stressed_sharpe_min, "stressed_sharpe"),
        (np.isfinite(worst_fold) and worst_fold >= thresholds.worst_fold_sharpe_min, "worst_fold_sharpe"),
        (np.isfinite(mdd) and abs(min(mdd, 0.0)) <= thresholds.max_drawdown_abs_max, "max_drawdown"),
        (np.isfinite(pre_corr) and pre_corr <= thresholds.archive_corr_pre_max, "archive_corr_pre"),
        (np.isfinite(recent_corr) and recent_corr <= thresholds.archive_corr_recent_max, "archive_corr_recent"),
        (np.isfinite(retention) and retention >= thresholds.delay_retention_min, "delay_retention"),
    ]
    failures = tuple(name for ok, name in checks if not ok)
    return ScreenResult(
        full_sharpe=sr,
        stressed_sharpe=stress_sr,
        worst_fold_sharpe=worst_fold,
        max_drawdown=mdd,
        archive_corr_pre=pre_corr,
        archive_corr_recent=recent_corr,
        delayed_sharpe=delayed_sr,
        delay_retention=retention,
        passed=not failures,
        failures=failures,
    )


def pareto_mask(values: np.ndarray, maximize: Sequence[bool]) -> np.ndarray:
    """Return nondominated rows for a dense metric matrix."""
    v = np.asarray(values, dtype=np.float64)
    if v.ndim != 2:
        raise ValueError("values must be 2D")
    maximize_arr = np.asarray(maximize, dtype=bool)
    if maximize_arr.size != v.shape[1]:
        raise ValueError("maximize length must equal number of columns")
    ok = np.isfinite(v).all(axis=1)
    w = v.copy()
    w[:, ~maximize_arr] *= -1.0
    keep = ok.copy()
    idx = np.flatnonzero(ok)
    for i in idx:
        if not keep[i]:
            continue
        dominated = np.any(
            np.all(w[idx] >= w[i], axis=1) & np.any(w[idx] > w[i], axis=1)
        )
        if dominated:
            keep[i] = False
    return keep
