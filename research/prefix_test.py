"""L2 prefix causality skeleton.

Compare strategy weights at time t when computed on data truncated at t
versus the full series prefix to t. Look-ahead ⇒ mismatch.

Requires qnt + real data for a full test. Without qnt, this module documents
the API and exits cleanly with TODO.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class PrefixCompareResult:
    ok: bool
    max_abs_diff: Optional[float]
    message: str


def compare_prefix_weights(
    weights_full_prefix: Any,
    weights_truncated: Any,
    *,
    atol: float = 1e-10,
    rtol: float = 1e-8,
) -> PrefixCompareResult:
    """Compare two weight arrays (numpy/xarray) for near-equality."""
    try:
        import numpy as np
    except ImportError:
        return PrefixCompareResult(False, None, "numpy required")

    a = np.asarray(
        getattr(weights_full_prefix, "values", weights_full_prefix), dtype=float
    )
    b = np.asarray(getattr(weights_truncated, "values", weights_truncated), dtype=float)
    if a.shape != b.shape:
        return PrefixCompareResult(
            False, None, f"shape mismatch {a.shape} vs {b.shape}"
        )
    diff = np.nanmax(np.abs(a - b))
    ok = bool(np.allclose(a, b, atol=atol, rtol=rtol, equal_nan=True))
    return PrefixCompareResult(ok, float(diff), "match" if ok else "mismatch")


def run_prefix_test(
    strategy_fn: Callable[[Any], Any],
    load_data_fn: Callable[[int], Any],
    *,
    lookback: int = 365,
    checkpoints: int = 3,
) -> PrefixCompareResult:
    """Skeleton end-to-end prefix test.

    TODO: when `qnt` is available, load successive prefixes and compare
    last-day weights from truncated panels vs sliced full multipass path.
    """
    try:
        import qnt  # noqa: F401
    except ImportError:
        return PrefixCompareResult(
            False,
            None,
            "TODO: qnt not installed — cannot run live prefix test. "
            "Use compare_prefix_weights() on synthetic panels, or install qnt "
            "and wire load_data_fn/strategy_fn checkpoints.",
        )

    # Minimal stub when qnt exists but full wiring is left to the researcher.
    _ = (strategy_fn, load_data_fn, lookback, checkpoints)
    return PrefixCompareResult(
        False,
        None,
        "TODO: implement checkpoint loop over cryptodaily prefixes; "
        "compare strategy(data[:t]) last-day weights vs reference.",
    )


if __name__ == "__main__":
    r = run_prefix_test(lambda d: d, lambda p: None)
    print(r.message)
    # Synthetic equality smoke check
    try:
        import numpy as np

        x = np.array([0.2, 0.3, 0.0])
        print(compare_prefix_weights(x, x))
    except ImportError:
        print("numpy missing — skip smoke compare")
    sys.exit(0)
