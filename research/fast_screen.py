"""Fast, deterministic screening primitives for deadline-scale Q25 research.

This module intentionally avoids Quantiacs/xarray strategy execution.  It accepts
already-computed daily candidate returns and a frozen return archive, then applies
cheap metrics/correlation gates before any candidate earns an exact replay.

The fast screen is NOT submission evidence.  Finalists must be reproduced by the
exact strategy implementation, full cost model, causality checks, multipass and
hosted uniqueness checks.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable, Mapping, Sequence

import numpy as np

TRADING_DAYS = 365.25


def _as_1d(x: Sequence[float]) -> np.ndarray:
    a = np.asarray(x, dtype=np.float64).reshape(-1)
    return a


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
    wealth = np.cumprod(1.0 + x)
    if wealth.size == 0:
        return float("nan")
    peaks = np.maximum.accumulate(wealth)
    dd = wealth / np.where(peaks > 0, peaks, np.nan) - 1.0
    return float(np.nanmin(dd))


def _standardize_cols(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return standardized columns and validity mask; NaNs are zero after centering.

    Correlation is intended for aligned return matrices with common date masks.
    The caller should construct archive windows consistently before using this.
    """
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    finite = np.isfinite(x)
    count = finite.sum(axis=0)
    sums = np.where(finite, x, 0.0).sum(axis=0)
    means = np.divide(sums, count, out=np.zeros_like(sums), where=count > 0)
    centered = np.where(finite, x - means, 0.0)
    ss = (centered * centered).sum(axis=0)
    scale = np.sqrt(ss)
    valid = (count >= 2) & np.isfinite(scale) & (scale > 0)
    z = np.zeros_like(centered)
    z[:, valid] = centered[:, valid] / scale[valid]
    return z, valid


def archive_correlations(candidate_returns: Sequence[float], archive_returns: np.ndarray) -> np.ndarray:
    """Fast candidate-vs-archive correlations by normalized matrix multiply.

    archive_returns shape: (time, strategies).  Input dates must already align.
    """
    c = _as_1d(candidate_returns)
    a = np.asarray(archive_returns, dtype=np.float64)
    if a.ndim != 2 or a.shape[0] != c.size:
        raise ValueError("archive_returns must have shape (len(candidate_returns), n_strategies)")
    cz, cvalid = _standardize_cols(c)
    az, avalid = _standardize_cols(a)
    out = np.full(a.shape[1], np.nan, dtype=np.float64)
    if cvalid[0]:
        out[avalid] = cz[:, 0] @ az[:, avalid]
    return out


def max_abs_archive_corr(candidate_returns: Sequence[float], archive_returns: np.ndarray) -> float:
    corrs = archive_correlations(candidate_returns, archive_returns)
    if not np.isfinite(corrs).any():
        return float("nan")
    return float(np.nanmax(np.abs(corrs)))


def residual_sharpe(candidate_returns: Sequence[float], core_returns: np.ndarray) -> float:
    """Sharpe of candidate residual after OLS on a core return matrix + intercept."""
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
    resid = yy - xx @ beta
    return annualized_sharpe(resid)


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

    failures: list[str] = []
    checks = [
        (np.isfinite(sr) and sr >= thresholds.full_sharpe_min, "full_sharpe"),
        (np.isfinite(stress_sr) and stress_sr >= thresholds.stressed_sharpe_min, "stressed_sharpe"),
        (np.isfinite(worst_fold) and worst_fold >= thresholds.worst_fold_sharpe_min, "worst_fold_sharpe"),
        (np.isfinite(mdd) and abs(min(mdd, 0.0)) <= thresholds.max_drawdown_abs_max, "max_drawdown"),
        (np.isfinite(pre_corr) and pre_corr <= thresholds.archive_corr_pre_max, "archive_corr_pre"),
        (np.isfinite(recent_corr) and recent_corr <= thresholds.archive_corr_recent_max, "archive_corr_recent"),
        (np.isfinite(retention) and retention >= thresholds.delay_retention_min, "delay_retention"),
    ]
    failures.extend(name for ok, name in checks if not ok)

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
        failures=tuple(failures),
    )


def pareto_mask(values: np.ndarray, maximize: Sequence[bool]) -> np.ndarray:
    """Return nondominated rows for a dense metric matrix.

    NaN rows are rejected.  Small O(n^2) implementation is deliberate: this is
    used only after cheap gates, where candidate count is expected to be modest.
    """
    v = np.asarray(values, dtype=np.float64)
    if v.ndim != 2:
        raise ValueError("values must be 2D")
    maximize = np.asarray(maximize, dtype=bool)
    if maximize.size != v.shape[1]:
        raise ValueError("maximize length must equal number of columns")
    ok = np.isfinite(v).all(axis=1)
    w = v.copy()
    w[:, ~maximize] *= -1.0
    keep = ok.copy()
    idx = np.flatnonzero(ok)
    for i in idx:
        if not keep[i]:
            continue
        dominated_by_any = np.any(
            np.all(w[idx] >= w[i], axis=1) & np.any(w[idx] > w[i], axis=1)
        )
        if dominated_by_any:
            keep[i] = False
    return keep
