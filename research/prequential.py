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


@dataclass(frozen=True)
class Origin:
    """Calendar-quarter scoring window with an explicit purged train boundary."""
    train_end: pd.Timestamp
    forward_start: pd.Timestamp
    forward_end: pd.Timestamp


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

    ``min_train_days`` counts the inclusive calendar span from ``train_start``
    through ``train_end``, matching :func:`quarterly_origins`. The score window
    starts strictly after the origin. Only origins whose full declared forward
    horizon has elapsed are returned, and no window crosses ``live_start``.
    Construction is deterministic and independent of returns. Calendar targets
    advance independently of observed timestamps so sparse Sponsor histories
    cannot stall the origin scheduler.
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
    first_origin_target = first + pd.Timedelta(days=min_train_days - 1)
    eligible = completed[completed >= first_origin_target]
    if len(eligible) == 0:
        return []

    origins: list[OriginWindow] = []
    target = eligible[0]
    previous_origin: pd.Timestamp | None = None
    while target < latest:
        origin_candidates = completed[completed <= target]
        if len(origin_candidates) == 0:
            break
        origin = origin_candidates[-1]
        # A sparse calendar can map several scheduled targets to the same last
        # observation. Advance the schedule, rather than re-emitting/stalling.
        if previous_origin is not None and origin <= previous_origin:
            target = target + pd.Timedelta(days=step_days)
            continue
        score_limit = origin + pd.Timedelta(days=forward_days)
        if score_limit > latest or score_limit >= live:
            break
        future = completed[completed > origin]
        if len(future) == 0:
            break
        score_start = future[0]
        score_candidates = completed[(completed >= score_start) & (completed <= score_limit)]
        if len(score_candidates) == 0:
            # The entire nominal score horizon may lie inside a Sponsor data
            # outage. That origin is not a completed scoring window, but it is
            # not evidence that later scheduled origins are unavailable.
            target = target + pd.Timedelta(days=step_days)
            continue
        score_end = score_candidates[-1]
        origins.append(OriginWindow(origin, first, origin, score_start, score_end))
        previous_origin = origin
        target = target + pd.Timedelta(days=step_days)

    return origins


def quarterly_origins(start, end, *, min_train_days=730, forward_days=90, purge_days=0):
    """Build deterministic completed quarterly windows with an explicit purge gap.

    ``min_train_days`` is measured from ``start`` through the inclusive
    ``train_end``. The first forward quarter is therefore the first quarter
    whose purged training boundary contains at least that much history.
    """
    start, end = pd.Timestamp(start).normalize(), pd.Timestamp(end).normalize()
    if end < start or min_train_days < 1 or forward_days < 1 or purge_days < 0:
        raise ValueError("invalid rolling-origin parameters")
    minimum_train_end = start + pd.Timedelta(days=min_train_days - 1)
    earliest_forward = minimum_train_end + pd.Timedelta(days=purge_days + 1)
    out = []
    for forward_start in pd.date_range(earliest_forward, end, freq="QS"):
        train_end = forward_start - pd.Timedelta(days=purge_days + 1)
        if (train_end - start).days + 1 < min_train_days:
            continue
        forward_end = forward_start + pd.Timedelta(days=forward_days - 1)
        if forward_end > end:
            continue
        out.append(Origin(train_end, forward_start, forward_end))
    return tuple(out)


def validate_origins(origins, *, minimum=8, purge_days=None):
    """Fail closed on chronology, purge separation, or insufficient origins."""
    if minimum < 1 or (purge_days is not None and purge_days < 0):
        raise ValueError("invalid validation parameters")
    if len(origins) < minimum:
        raise ValueError(f"need at least {minimum} completed origins, got {len(origins)}")
    previous = None
    for origin in origins:
        if not origin.train_end < origin.forward_start <= origin.forward_end:
            raise ValueError("non-causal origin")
        if purge_days is not None:
            observed_gap = (origin.forward_start - origin.train_end).days - 1
            if observed_gap != purge_days:
                raise ValueError(f"purge mismatch: expected {purge_days} days, got {observed_gap}")
        if previous is not None and origin.forward_start <= previous:
            raise ValueError("origins are not strictly chronological")
        previous = origin.forward_start


def exponential_recency_weights(timestamps: Iterable[object], *, half_life_days: float = 730.0, as_of: str | pd.Timestamp | None = None) -> pd.Series:
    """Return normalized causal recency weights for already-observed dates."""
    if half_life_days <= 0:
        raise ValueError("half_life_days must be positive")
    idx = _dates(timestamps)
    cutoff = pd.Timestamp(as_of) if as_of is not None else idx[-1]
    if (idx > cutoff).any():
        raise ValueError("timestamps after as_of are future observations")
    age_days = np.asarray((cutoff - idx).days, dtype=float)
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
