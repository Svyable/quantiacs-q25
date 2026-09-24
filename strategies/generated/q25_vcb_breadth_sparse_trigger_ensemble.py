"""Frozen portfolio-level sparse-trigger execution for the VCB x breadth ensemble."""
from __future__ import annotations

import numpy as np
import xarray as xr

TRIGGER_DISPLACEMENT = 0.05


def apply_sparse_trigger(
    target: xr.DataArray,
    eligible: xr.DataArray,
    threshold: float = TRIGGER_DISPLACEMENT,
) -> xr.DataArray:
    """Hold weights until eligible target displacement reaches the frozen threshold.

    Sponsor liquidity eligibility is a hard constraint: positions in ineligible assets
    are exited immediately and are never retained merely to suppress turnover.
    Displacement is one-way portfolio turnover, 0.5 * sum(abs(target - held)).
    """
    if threshold < 0:
        raise ValueError("threshold must be non-negative")
    target, eligible = xr.align(target, eligible, join="exact")
    target = target.fillna(0).clip(min=0)
    eligible = eligible.fillna(0) > 0
    target = target.where(eligible, 0)
    gross = target.sum("asset")
    target = xr.where(gross > 1.0, target / gross, target)

    values = np.asarray(target.transpose("time", "asset").values, dtype=float)
    mask = np.asarray(eligible.transpose("time", "asset").values, dtype=bool)
    out = np.zeros_like(values)
    held = np.zeros(values.shape[1], dtype=float)
    for i in range(values.shape[0]):
        forced = held.copy()
        forced[~mask[i]] = 0.0
        desired = values[i]
        displacement = 0.5 * float(np.abs(desired - forced).sum())
        held = desired.copy() if displacement >= threshold else forced
        out[i] = held
    result = xr.DataArray(
        out,
        coords={"time": target.time, "asset": target.asset},
        dims=("time", "asset"),
    )
    return result.transpose(*target.dims)
