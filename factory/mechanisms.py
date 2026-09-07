"""Expanded mechanism families for Q25 research (inspiration only — no affiliation).

Use these ids in preregistration, desks, and dual-track experiments.
Families describe *what* is tested; they do not claim empirical edge.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MechanismFamily:
    id: str
    name: str
    description: str
    typical_track: str  # "discovery" | "robustness" | "both"
    falsifier_hint: str


MECHANISM_FAMILIES: dict[str, MechanismFamily] = {
    "momentum": MechanismFamily(
        id="momentum",
        name="Time-series momentum",
        description="Trend continuation via SMA/EMA/returns lookbacks on liquid names.",
        typical_track="both",
        falsifier_hint="Sign-flip of trend signal destroys IS edge; lag-1 break removes edge.",
    ),
    "breakout": MechanismFamily(
        id="breakout",
        name="Breakout / Donchian",
        description="Enter on N-day high/low breaks among liquid assets.",
        typical_track="both",
        falsifier_hint="Randomizing breakout day within window nulls edge.",
    ),
    "quality_persistence": MechanismFamily(
        id="quality_persistence",
        name="Quality / persistence",
        description="Persistence of relative performance or low-churn winners.",
        typical_track="discovery",
        falsifier_hint="Edge vanishes when persistence window is shuffled.",
    ),
    "breadth": MechanismFamily(
        id="breadth",
        name="Market breadth",
        description="Universe-level advance/decline or % above MA as risk-on gate.",
        typical_track="both",
        falsifier_hint="Gate with inverted breadth should not improve risk-adjusted outcomes.",
    ),
    "xs_rs": MechanismFamily(
        id="xs_rs",
        name="Cross-sectional relative strength",
        description="Long top-K liquid names by relative return / rank.",
        typical_track="both",
        falsifier_hint="Bottom-K long should not outperform top-K if RS is causal.",
    ),
    "downside_asymmetry": MechanismFamily(
        id="downside_asymmetry",
        name="Downside asymmetry",
        description="Prefer names with favorable upside/downside return asymmetry.",
        typical_track="discovery",
        falsifier_hint="Using upside-only volatility should not replicate the signal.",
    ),
    "residual_momentum": MechanismFamily(
        id="residual_momentum",
        name="Residual momentum",
        description="Momentum after neutralizing market / simple core factor.",
        typical_track="discovery",
        falsifier_hint="Residual equals raw momentum (no unique component).",
    ),
    "co_crash": MechanismFamily(
        id="co_crash",
        name="Co-crash / crash comovement",
        description="Avoid or underweight names that co-crash with the basket.",
        typical_track="discovery",
        falsifier_hint="Crash-comovement ranks are unstable out of sample / null under shuffle.",
    ),
    "dispersion": MechanismFamily(
        id="dispersion",
        name="Cross-sectional dispersion",
        description="Allocate more when dispersion is high (or regime-conditioned).",
        typical_track="discovery",
        falsifier_hint="Dispersion timing with inverted signal should not help.",
    ),
    "volume_price": MechanismFamily(
        id="volume_price",
        name="Volume / price confirmation",
        description="Trend or RS confirmed by volume expansion (OHLCV only).",
        typical_track="both",
        falsifier_hint="Volume gate with random volume series leaves performance unchanged.",
    ),
    "vol_state": MechanismFamily(
        id="vol_state",
        name="Volatility state",
        description="Vol-targeting, inverse-vol weights, or high-vol risk-off.",
        typical_track="both",
        falsifier_hint="Constant vol vs targeted vol: no risk difference if state unused.",
    ),
    "liquidity_lifecycle": MechanismFamily(
        id="liquidity_lifecycle",
        name="Liquidity lifecycle",
        description="Enter/exit with is_liquid transitions; avoid newly liquid churn traps.",
        typical_track="robustness",
        falsifier_hint="Ignoring is_liquid transitions should not improve if lifecycle matters.",
    ),
    "path_efficiency": MechanismFamily(
        id="path_efficiency",
        name="Path efficiency",
        description="Kaufman-like efficiency / range compression-expansion.",
        typical_track="discovery",
        falsifier_hint="Efficiency threshold noise-matched should not separate outcomes.",
    ),
    "serial_dependence": MechanismFamily(
        id="serial_dependence",
        name="Serial dependence",
        description="Short-horizon autocorrelation / reversal within liquid set.",
        typical_track="discovery",
        falsifier_hint="Lag shuffle destroys claimed serial dependence.",
    ),
    "concentration": MechanismFamily(
        id="concentration",
        name="Concentration control",
        description="Caps, water-fill, and diversification constraints as first-class design.",
        typical_track="robustness",
        falsifier_hint="Uncapped equal-weight among signals worsens cost/DD if caps matter.",
    ),
    "beta_residual_beta": MechanismFamily(
        id="beta_residual_beta",
        name="Beta / residual beta",
        description="Market-beta conditioning or residual-beta tilts (crypto basket proxy).",
        typical_track="discovery",
        falsifier_hint="Beta sort inverted should not preserve residual claim.",
    ),
    "shock_recovery": MechanismFamily(
        id="shock_recovery",
        name="Shock recovery",
        description="Re-entry after large drawdown/shock with confirmation.",
        typical_track="discovery",
        falsifier_hint="Random re-entry delays match claimed recovery premium.",
    ),
    "price_delay": MechanismFamily(
        id="price_delay",
        name="Price delay / slow diffusion",
        description="Delayed adjustment across liquid names (lead-lag style, Quantiacs fields only).",
        typical_track="discovery",
        falsifier_hint="Lead-lag with shuffled leaders nulls edge.",
    ),
    "regime_conditioned": MechanismFamily(
        id="regime_conditioned",
        name="Regime-conditioned",
        description="Signal on only in predeclared vol/trend/breadth regimes.",
        typical_track="both",
        falsifier_hint="Opposite regime mask should not improve if conditioning is real.",
    ),
}


def list_mechanisms() -> list[MechanismFamily]:
    return list(MECHANISM_FAMILIES.values())


def get_mechanism(mechanism_id: str) -> MechanismFamily:
    if mechanism_id not in MECHANISM_FAMILIES:
        raise KeyError(
            f"Unknown mechanism: {mechanism_id}. Known: {sorted(MECHANISM_FAMILIES)}"
        )
    return MECHANISM_FAMILIES[mechanism_id]


def mechanism_ids() -> list[str]:
    return sorted(MECHANISM_FAMILIES)
