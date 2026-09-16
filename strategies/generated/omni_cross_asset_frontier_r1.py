"""Implementation repair for omni_cross_asset_frontier_20260915.

The original frozen implementation failed its synthetic pre-market test because
Pandas produced an object-dtype Series in one robust-normalization path and
NumPy tanh rejected it. No market returns for the new families were measured.

This wrapper changes no research formula, parameter, window, threshold, panel,
portfolio rule, or test criterion. It only replaces `_robust_unit` with an
explicit numeric-float implementation and then delegates every other operation
to the frozen research driver.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


BASE_PATH = Path(__file__).with_name("omni_cross_asset_frontier.py")
spec = importlib.util.spec_from_file_location("omni_frontier_base", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load frozen OMNI frontier implementation")
BASE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(BASE)


def _robust_unit(series: pd.Series) -> pd.Series:
    """Formula-identical robust [0,1] mapping with explicit float dtype."""
    source = pd.to_numeric(series, errors="coerce").astype(float)
    center = source.rolling(BASE.NORM_WINDOW, min_periods=BASE.NORM_MIN).median()
    q75 = source.rolling(BASE.NORM_WINDOW, min_periods=BASE.NORM_MIN).quantile(0.75)
    q25 = source.rolling(BASE.NORM_WINDOW, min_periods=BASE.NORM_MIN).quantile(0.25)
    sigma = ((q75 - q25) / 1.349).clip(lower=1e-8).astype(float)
    z = ((source - center) / sigma).clip(-8.0, 8.0).astype(float)
    mapped = 0.5 + 0.5 * np.tanh(z.to_numpy(dtype=float) / 2.0)
    return pd.Series(mapped, index=z.index, dtype=float).where(z.notna())


# Functions in BASE resolve globals from BASE.__dict__, so this surgical patch
# repairs every preregistered family's robust transform without changing its
# implementation or parameters.
BASE._robust_unit = _robust_unit

# Re-export for tests and research use.
_stock_context = BASE._stock_context
_tail_dependence = BASE._tail_dependence
_fragility_recovery = BASE._fragility_recovery
_online_ridge = BASE._online_ridge
_risk_to_weights = BASE._risk_to_weights
run = BASE.run


def main() -> None:
    BASE.main()


if __name__ == "__main__":
    main()
