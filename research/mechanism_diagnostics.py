"""Paired diagnostics that separate an interesting signal from deployable alpha.

Bootstrap intervals describe development uncertainty, not selection-adjusted
significance. They never feed allocations or change the promotion gates.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def allocation_difference(parent, control, tolerance=1e-10):
    if parent.dims != control.dims or not parent.time.equals(control.time) or not parent.asset.equals(control.asset):
        raise ValueError('target paths must have exactly matching coordinates')
    delta = np.abs(parent.values - control.values)
    if delta.size == 0 or not np.isfinite(delta).all():
        raise ValueError('nonempty finite target paths required')
    changed = delta > tolerance
    return dict(status='IDENTICAL_TARGETS' if not changed.any() else 'DISTINCT_TARGETS',
                changed_days=int(changed.any(axis=1).sum()),
                changed_day_fraction=float(changed.any(axis=1).mean()),
                mean_absolute_gross_difference=float(delta.sum(axis=1).mean()),
                max_cell_difference=float(delta.max()))


def paired_block_interval(parent, control, block_days=21, replicates=2000, seed=20260910):
    """Circular moving-block bootstrap of matched daily net return differences.

    Strict alignment avoids silently compressing missing days into adjacent
    observations. A block spans 21 chronological days, not 21 nonmissing rows.
    """
    if block_days < 1 or replicates < 100:
        raise ValueError('positive block size and at least 100 replicates required')
    if not parent.index.equals(control.index):
        raise ValueError('return dates must match exactly')
    times = pd.DatetimeIndex(parent.index)
    if times.has_duplicates or not times.is_monotonic_increasing:
        raise ValueError('unique increasing return dates required')
    if len(times) > 1 and not np.all(np.diff(times.values) == np.timedelta64(1, 'D')):
        raise ValueError('daily contiguous return dates required')
    difference = parent.to_numpy(dtype=float) - control.to_numpy(dtype=float)
    if not np.isfinite(difference).all():
        raise ValueError('finite matched returns required')
    n = len(difference)
    if n < max(126, 2 * block_days):
        return dict(status='PENDING_INSUFFICIENT_MATCHED_RETURNS', observations=n)
    rng = np.random.default_rng(seed)
    blocks = (n + block_days - 1) // block_days
    starts = rng.integers(0, n, (replicates, blocks))
    index = (starts[:, :, None] + np.arange(block_days)) % n
    draws = difference[index.reshape(replicates, -1)[:, :n]].mean(axis=1) * 365
    low, high = np.quantile(draws, [.025, .975])
    return dict(status='DEVELOPMENT_DIAGNOSTIC_ONLY', observations=n,
                annualized_mean_difference=float(difference.mean() * 365),
                percentile_95_interval=[float(low), float(high)],
                block_days=block_days, replicates=replicates, seed=seed,
                selection_adjusted=False)
