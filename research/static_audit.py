"""L0/L1 static admissibility checks on weight arrays.

Pure functions intended to run without `qnt`. Prefer xarray when available;
fall back to documented stubs / numpy-shaped checks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, List, Optional

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None  # type: ignore

try:
    import xarray as xr
except ImportError:  # pragma: no cover
    xr = None  # type: ignore


@dataclass
class AuditResult:
    ok: bool
    checks: dict[str, bool] = field(default_factory=dict)
    messages: List[str] = field(default_factory=list)

    def fail(self, name: str, msg: str) -> None:
        self.checks[name] = False
        self.messages.append(msg)
        self.ok = False

    def pass_(self, name: str, msg: str = "") -> None:
        self.checks[name] = True
        if msg:
            self.messages.append(msg)


def _as_numpy(weights: Any):
    if np is None:
        raise ImportError("numpy required for static_audit")
    if xr is not None and isinstance(weights, xr.DataArray):
        return np.asarray(weights.values, dtype=float)
    return np.asarray(weights, dtype=float)


def check_finite(weights: Any) -> bool:
    arr = _as_numpy(weights)
    return bool(np.isfinite(arr).all())


def check_long_only(weights: Any, atol: float = 1e-12) -> bool:
    arr = _as_numpy(weights)
    return bool((arr >= -atol).all())


def check_gross_le_one(weights: Any, atol: float = 1e-9) -> bool:
    """Gross exposure <= 1 along asset axis; cash permitted (gross < 1 OK).

    Assumes last axis is assets when ndim >= 1. For 0-d, treats scalar as exposure.
    """
    arr = _as_numpy(weights)
    if arr.ndim == 0:
        return bool(arr <= 1.0 + atol)
    gross = np.nansum(np.abs(arr), axis=-1)
    return bool((gross <= 1.0 + atol).all())


def check_liquid_mask(weights: Any, is_liquid: Any, atol: float = 1e-12) -> bool:
    """Non-zero weights only where is_liquid is truthy."""
    w = _as_numpy(weights)
    liq = _as_numpy(is_liquid)
    if w.shape != liq.shape:
        raise ValueError(f"shape mismatch weights {w.shape} vs is_liquid {liq.shape}")
    illegal = (np.abs(w) > atol) & (liq <= 0)
    return not bool(illegal.any())


def audit_weights(
    weights: Any,
    is_liquid: Optional[Any] = None,
    *,
    require_gross_le_one: bool = True,
) -> AuditResult:
    """Run L0 static checks. Returns AuditResult (ok + per-check flags)."""
    result = AuditResult(ok=True)
    if np is None:
        result.fail("numpy", "numpy not installed — cannot audit")
        return result

    if check_finite(weights):
        result.pass_("finite")
    else:
        result.fail("finite", "weights contain NaN or Inf")

    if check_long_only(weights):
        result.pass_("long_only")
    else:
        result.fail("long_only", "negative weights present (long-only required)")

    if require_gross_le_one:
        if check_gross_le_one(weights):
            result.pass_("gross_le_one")
        else:
            result.fail("gross_le_one", "gross exposure exceeds 1")

    if is_liquid is not None:
        try:
            if check_liquid_mask(weights, is_liquid):
                result.pass_("liquid_only")
            else:
                result.fail("liquid_only", "non-zero weight on non-liquid asset")
        except ValueError as e:
            result.fail("liquid_only", str(e))

    return result


def synthetic_panel(n_time: int = 5, n_asset: int = 4):
    """Build a tiny synthetic xarray panel for L1 tests (no qnt)."""
    if xr is None or np is None:
        raise ImportError(
            "xarray and numpy required for synthetic_panel. "
            "Install them or skip L1 synthetic tests."
        )
    time = np.arange(n_time)
    asset = [f"A{i}" for i in range(n_asset)]
    # Equal weight among first 3 assets, last illiquid → will fail liquid if used raw
    w = np.zeros((n_time, n_asset))
    w[:, :3] = 1.0 / 3.0
    weights = xr.DataArray(w, dims=("time", "asset"), coords={"time": time, "asset": asset})
    liq = np.ones((n_time, n_asset))
    liq[:, -1] = 0.0
    is_liquid = xr.DataArray(liq, dims=("time", "asset"), coords=weights.coords)
    return weights, is_liquid


def _self_test() -> None:
    """Minimal L1 deterministic tests without qnt."""
    if np is None:
        print("SKIP: numpy missing")
        return
    w = np.array([[0.5, 0.5, 0.0], [0.2, 0.2, 0.2]])
    assert check_long_only(w)
    assert check_gross_le_one(w)
    assert check_finite(w)
    liq = np.array([[1, 1, 0], [1, 1, 1]])
    assert check_liquid_mask(w, liq)
    bad = w.copy()
    bad[0, 2] = 0.1
    assert not check_liquid_mask(bad, liq)
    if xr is not None:
        weights, is_liquid = synthetic_panel()
        # zero out illiquid column
        weights = weights * is_liquid
        r = audit_weights(weights, is_liquid)
        assert r.ok, r.messages
    print("static_audit self-test OK")


if __name__ == "__main__":
    _self_test()
