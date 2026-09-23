"""Reusable causal rolling-origin utilities for Research Mandate V2.

This module defines chronology only. It does not fit models, choose assets, or
inspect future outcomes when constructing an origin.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class OriginWindow:
    origin: pd.Timestamp
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    score_start: pd.Timestamp
    score_end: pd.Timestamp

    def as_dict(self) -> dict[str, str]:
        return {
            "origin": self.origin.strftime("%Y-%m-%d"),
            "train_start": self.train_start.strftime("%Y-%m-%d"),
            "train_end": self.train_end.strftime("%Y-%m-%d"),
            "score_start": self.score_start.strftime("%Y-%m-%d"),
            "score_end": self.score_end.strftime("%Y-%m-%d"),
        }


def _dates(values: Iterable[object]) -> pd.DatetimeIndex:
    idx = pd.DatetimeIndex(pd.to_datetime(list(values))).sort_values().unique()
    if len(idx) < 2:
        raise ValueError("at least two timestamps are required")
    if idx.hasnans:
        raise ValueError("timestamps must be finite")
    return idx


def rolling_origins(
    timestamps: Iterable[object],
    *,
    min_train_days: int = 365,
    forward_days: int = 90,
    step_days: int = 90,
    live_start: str | pd.Timestamp = "2026-10-01",
) -> list[OriginWindow]:
    """Build expanding-window prequential origins from completed history.

    The score window starts strictly after the origin. No window crosses
    live_start. Construction is deterministic and independent of returns.
    """
    if min_train_days <= 0 or forward_days <= 0 or step_days <= 0:
        raise ValueError("window lengths must be positive")

    idx = _dates(timestamps)
    live = pd.Timestamp(live_start)
    completed = idx[idx < live]
    if len(completed) < 2:
        return []

    first = completed[0]
    latest = completed[-1]
    first_origin_target = first + pd.Timedelta(days=min_train_days)
    eligible = completed[completed >= first_origin_target]
    if len(eligible) == 0:
        return []

    origins: list[OriginWindow] = []
    target = eligible[0]
    while target < latest:
        origin_candidates = completed[completed <= target]
        if len(origin_candidates) == 0:
            break
        origin = origin_candidates[-1]
        future = completed[completed > origin]
        if len(future) == 0:
            break
        score_start = future[0]
        score_limit = origin + pd.Timedelta(days=forward_days)
        score_candidates = completed[(completed >= score_start) & (completed <= score_limit)]
        if len(score_candidates) == 0:
            break
        score_end = score_candidates[-1]
        origins.append(
            OriginWindow(
                origin=origin,
                train_start=first,
                train_end=origin,
                score_start=score_start,
                score_end=score_end,
            )
        )
        target = origin + pd.Timedelta(days=step_days)
        if target <= origin:
            raise RuntimeError("origin schedule did not advance")

    unique: dict[pd.Timestamp, OriginWindow] = {}
    for window in origins:
        unique[window.origin] = window
    return list(unique.values())


def exponential_recency_weights(
    timestamps: Iterable[object],
    *,
    half_life_days: float = 730.0,
    as_of: str | pd.Timestamp | None = None,
) -> pd.Series:
    """Return normalized causal recency weights for already-observed dates."""
    if half_life_days <= 0:
        raise ValueError("half_life_days must be positive")
    idx = _dates(timestamps)
    cutoff = pd.Timestamp(as_of) if as_of is not None else idx[-1]
    if (idx > cutoff).any():
        raise ValueError("timestamps after as_of are future observations")
    age_days = (cutoff - idx).days.astype(float)
    raw = np.exp(-np.log(2.0) * age_days / float(half_life_days))
    raw = raw / raw.sum()
    return pd.Series(raw, index=idx, name="recency_weight")


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    """Align and compute a finite weighted mean without silent imputation."""
    x, w = values.align(weights, join="inner")
    mask = np.isfinite(x.to_numpy(dtype=float)) & np.isfinite(w.to_numpy(dtype=float))
    if not mask.any():
        raise ValueError("no finite aligned observations")
    xv = x.to_numpy(dtype=float)[mask]
    wv = w.to_numpy(dtype=float)[mask]
    total = float(wv.sum())
    if total <= 0:
        raise ValueError("aligned weights must have positive mass")
    return float(np.dot(xv, wv) / total)
