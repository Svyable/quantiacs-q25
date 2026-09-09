"""Mechanism families for Q25 research (inspiration only — no affiliation).

Use these ids in preregistration, desks, and dual-track experiments.
Families describe *what* is tested; they do not claim empirical edge.

Important: this catalog contains both crowded controls and open frontier areas.
Before treating a family as new alpha, consult configs/research_frontier.yaml and
configs/external_research_leads.yaml, then compare the proposal with the incumbent
roster on information primitive, transform, timing/state, and portfolio construction.
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
        description="Trend continuation via SMA/EMA/returns lookbacks on liquid names; crowded control family.",
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
        description="Universe-level advance/decline or % above MA as risk-on gate; simple forms are already occupied.",
        typical_track="both",
        falsifier_hint="Gate with inverted breadth should not improve risk-adjusted outcomes.",
    ),
    "xs_rs": MechanismFamily(
        id="xs_rs",
        name="Cross-sectional relative strength",
        description="Long top-K liquid names by relative return / rank; use primarily as a control unless materially transformed.",
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
        description="Momentum after neutralizing market / simple core factor; already represented in incumbent research.",
        typical_track="discovery",
        falsifier_hint="Residual equals raw momentum or loses incremental value versus incumbents.",
    ),
    "co_crash": MechanismFamily(
        id="co_crash",
        name="Co-crash / crash comovement",
        description="Avoid or underweight names that co-crash with the basket; static forms are occupied by CoCrash126.",
        typical_track="discovery",
        falsifier_hint="Crash-comovement ranks are unstable out of sample / null under shuffle.",
    ),
    "dispersion": MechanismFamily(
        id="dispersion",
        name="Cross-sectional dispersion",
        description="Allocate more when dispersion is high (or regime-conditioned); simple residual-dispersion timing is occupied.",
        typical_track="discovery",
        falsifier_hint="Dispersion timing with inverted signal should not help.",
    ),
    "volume_price": MechanismFamily(
        id="volume_price",
        name="Volume / price confirmation",
        description="Trend or RS confirmed by volume expansion (OHLCV only); simple confirmation is a crowded control.",
        typical_track="both",
        falsifier_hint="Volume gate with randomized volume series leaves performance unchanged.",
    ),
    "vol_state": MechanismFamily(
        id="vol_state",
        name="Volatility state",
        description="Vol-targeting, inverse-vol weights, or high-vol risk-off; basic risk scaling is a control rather than frontier alpha.",
        typical_track="both",
        falsifier_hint="Constant vol vs targeted vol: no risk difference if state unused.",
    ),
    "vol_term_structure": MechanismFamily(
        id="vol_term_structure",
        name="Volatility term structure / vol-of-vol",
        description="Use the shape, slope, curvature, acceleration or instability of short/medium/long realized-volatility horizons as an alpha or deployment state.",
        typical_track="both",
        falsifier_hint="Replacing the term structure with a single realized-vol level preserves the claimed edge.",
    ),
    "liquidity_lifecycle": MechanismFamily(
        id="liquidity_lifecycle",
        name="Liquidity lifecycle",
        description="Enter/exit with is_liquid transitions; V11 already occupies simple positive-entry lifecycle events.",
        typical_track="robustness",
        falsifier_hint="Ignoring is_liquid transitions should not improve if lifecycle matters.",
    ),
    "liquidity_hysteresis": MechanismFamily(
        id="liquidity_hysteresis",
        name="Liquidity-transition hysteresis",
        description="Model age since entry, re-entry, repeated eligibility transitions and maturation/decay around historical is_liquid changes.",
        typical_track="both",
        falsifier_hint="Randomizing transition ages while preserving current membership should destroy the effect.",
    ),
    "path_efficiency": MechanismFamily(
        id="path_efficiency",
        name="Path efficiency",
        description="Kaufman-like efficiency / range compression-expansion; plain efficiency-ratio trend is already represented.",
        typical_track="discovery",
        falsifier_hint="Efficiency threshold noise-matched should not separate outcomes.",
    ),
    "range_volume_geometry": MechanismFamily(
        id="range_volume_geometry",
        name="Range-volume geometry",
        description="Interactions among high-low range, close location, abnormal volume, path curvature and compression/expansion state transitions.",
        typical_track="discovery",
        falsifier_hint="Destroying the range/close-location interaction while preserving trend and volume should remove the effect.",
    ),
    "price_elasticity": MechanismFamily(
        id="price_elasticity",
        name="Price-volume elasticity / absorption",
        description="Self-asset directional or range displacement relative to abnormal dollar volume, close location and path geometry; distinguish absorption/exhaustion from efficient or fragile repricing.",
        typical_track="discovery",
        falsifier_hint="Randomly re-pair price displacement and volume ranks while preserving marginals; the effect should disappear if the interaction is causal.",
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
        name="Shock recovery surface",
        description="Model depth, time-since-shock, recovery slope, failed recovery and breadth rather than blind dip-buying.",
        typical_track="discovery",
        falsifier_hint="Random matched-frequency shock dates or recovery delays match the claimed recovery premium.",
    ),
    "price_delay": MechanismFamily(
        id="price_delay",
        name="Assimilation delay / slow diffusion",
        description="Changes in how quickly assets or cohorts absorb market/cross-asset shocks, including lag compression and leader/follower turnover.",
        typical_track="discovery",
        falsifier_hint="Shuffling leaders/lags while preserving marginal returns leaves the edge intact.",
    ),
    "correlation_topology": MechanismFamily(
        id="correlation_topology",
        name="Residual correlation topology",
        description="Dynamic graph structure: centrality migration, clustering, bridge nodes, eigenvalue concentration, fragmentation and reconnection.",
        typical_track="discovery",
        falsifier_hint="A static low-correlation or low-beta sort reproduces the claimed topology edge.",
    ),
    "tail_dependence": MechanismFamily(
        id="tail_dependence",
        name="Tail dependence state",
        description="Downside co-exceedance, semivariance, lower-tail rank dependence, drawdown duration and recovery asymmetry beyond static skew/co-crash.",
        typical_track="discovery",
        falsifier_hint="Replacing lower-tail state with ordinary variance/correlation preserves the result.",
    ),
    "higher_moments": MechanismFamily(
        id="higher_moments",
        name="Higher-moment residual structure",
        description="Residual skew/kurtosis and changes in higher moments; raw low residual skew is already explored, so new work needs a distinct state or interaction.",
        typical_track="discovery",
        falsifier_hint="Mean/variance controls explain the same cross-sectional ranking or the higher-moment state is unstable out of sample.",
    ),
    "nonlinear_response": MechanismFamily(
        id="nonlinear_response",
        name="Nonlinear cross-sectional response",
        description="Threshold, saturation, sign-asymmetric or state-dependent leader/follower response using causal OHLCV histories.",
        typical_track="discovery",
        falsifier_hint="A linear response model explains the same return stream and state dependence disappears under sign/threshold ablation.",
    ),
    "forecast_surprise": MechanismFamily(
        id="forecast_surprise",
        name="Online forecast surprise",
        description="Use the causal error of a tiny rolling forecast as an information primitive: signed surprise, standardized error, calibration drift or surprise half-life beyond raw residual return.",
        typical_track="discovery",
        falsifier_hint="Replacing model surprise with raw residual return or shuffled predictions preserves the result.",
    ),
    "forecast_disagreement": MechanismFamily(
        id="forecast_disagreement",
        name="Forecast disagreement / calibration state",
        description="Use disagreement among two or three deliberately different simple causal models as an uncertainty, opportunity or gross-risk state.",
        typical_track="both",
        falsifier_hint="Permuting model identities or replacing disagreement with ordinary return dispersion gives the same deployment benefit.",
    ),
    "onchain_state": MechanismFamily(
        id="onchain_state",
        name="On-chain network state × cross-section",
        description="Condition automatic cross-sectional crypto selection on Quantiacs-provided blockchain/network state, only after current Q25 admissibility and timestamp semantics are verified.",
        typical_track="discovery",
        falsifier_hint="Matched-frequency market-volatility states or shuffled network-state dates reproduce the effect.",
    ),
    "index_ecology": MechanismFamily(
        id="index_ecology",
        name="CRYPTO10 benchmark-composition ecology",
        description="If current Q25 rules permit historical benchmark weights, study concentration, member weight migration, entry maturation and leadership turnover rather than static benchmark holding.",
        typical_track="discovery",
        falsifier_hint="Binary is_liquid transitions or shuffled within-date benchmark-weight changes explain the same effect.",
    ),
    "persistent_low_vol_control": MechanismFamily(
        id="persistent_low_vol_control",
        name="Persistent low-volatility external control",
        description="Simple cross-sectional realized-volatility rank selector reproduced independently as a control, not a frontier novelty claim.",
        typical_track="robustness",
        falsifier_hint="Equal-liquid or ordinary inverse-vol controls provide the same result and residual value versus defensive incumbents is absent.",
    ),
    "opportunity_density": MechanismFamily(
        id="opportunity_density",
        name="Opportunity density / alpha breadth",
        description="Predict whether the cross-section contains enough independent opportunity to justify concentration or gross risk.",
        typical_track="both",
        falsifier_hint="Randomized rank stability or mechanism disagreement produces the same cash/gross timing benefit.",
    ),
    "execution_aware_alpha": MechanismFamily(
        id="execution_aware_alpha",
        name="Execution-aware alpha density",
        description="Trade only when expected signal improvement is large relative to ATR-linked turnover cost and persistence state.",
        typical_track="robustness",
        falsifier_hint="Post-hoc smoothing without alpha-per-cost conditioning gives the same result.",
    ),
    "regime_conditioned": MechanismFamily(
        id="regime_conditioned",
        name="Regime-conditioned",
        description="Signal active only in predeclared vol/trend/breadth regimes; generic regime gating is already used widely, so require a mechanism-specific interaction.",
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
