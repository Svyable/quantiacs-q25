"""Dual research tracks: DISCOVERY vs ROBUSTNESS.

Both tracks are required. Independent convergence on the same mechanism
is stronger evidence than either track alone.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Track:
    id: str
    name: str
    capacity: str
    design_rules: tuple[str, ...]
    preferred_mechanisms: tuple[str, ...]
    notes: str


DISCOVERY = Track(
    id="discovery",
    name="Discovery — high-capacity alpha factory",
    capacity="high",
    design_rules=(
        "Rich feature ensembles allowed (breakout, flow, tail, risk-guards)",
        "Heavier multiple-testing burden — preregister and ledger every look",
        "Residual / originality checks mandatory before promotion",
        "Still: Quantiacs data only, long-only * is_liquid, no hand-picked coins",
    ),
    preferred_mechanisms=(
        "momentum",
        "breakout",
        "quality_persistence",
        "xs_rs",
        "downside_asymmetry",
        "residual_momentum",
        "co_crash",
        "dispersion",
        "volume_price",
        "vol_state",
        "path_efficiency",
        "serial_dependence",
        "beta_residual_beta",
        "shock_recovery",
        "price_delay",
        "regime_conditioned",
        "breadth",
    ),
    notes="Optimize for unique causal mechanisms, not peak IS Sharpe clones.",
)

ROBUSTNESS = Track(
    id="robustness",
    name="Robustness — deliberately simple",
    capacity="low",
    design_rules=(
        "Few bounded signals",
        "Weekly rebalance (reduce ATR-linked cost)",
        "Permit cash (gross < 1 OK)",
        "Capped water-fill allocation (unused capacity stays cash)",
        "Long-only * is_liquid",
        "No hand-picked assets",
        "Execution delay left to evaluator",
        "Optional modules: market-risk guards, vol targeting, drawdown fades, turnover smoothing",
    ),
    preferred_mechanisms=(
        "momentum",
        "breakout",
        "xs_rs",
        "vol_state",
        "liquidity_lifecycle",
        "concentration",
        "breadth",
        "volume_price",
        "regime_conditioned",
    ),
    notes="Baseline sketch: strategies/robust_weekly_waterfill.py (no metrics claimed).",
)

TRACKS: dict[str, Track] = {
    DISCOVERY.id: DISCOVERY,
    ROBUSTNESS.id: ROBUSTNESS,
}


def list_tracks() -> list[Track]:
    return list(TRACKS.values())


def get_track(track_id: str) -> Track:
    if track_id not in TRACKS:
        raise KeyError(f"Unknown track: {track_id}. Known: {sorted(TRACKS)}")
    return TRACKS[track_id]
