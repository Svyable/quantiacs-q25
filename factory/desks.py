"""Idea desks inspired by quant-shop styles (NOT affiliated).

Desks are idea generators / alpha-family prompts. Names evoke desk cultures
(AQR / WorldQuant / Jump / Two Sigma / Point72 / Cumberland / DRW) as stylistic
anchors only — this project has no affiliation with those firms.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Desk:
    """A research desk that proposes alpha families and param ranges."""

    id: str
    name: str
    style_prompt: str
    alpha_families: tuple[str, ...]
    default_template: str = "strategy_multipass"
    notes: str = ""


@dataclass
class IdeaSpec:
    """Lightweight proposal emitted by a desk (before Idea materialization)."""

    name: str
    desk_id: str
    family: str
    thesis: str
    params: dict[str, Any]
    param_ranges: dict[str, tuple[float, float]]
    template_id: str = "strategy_multipass"
    tags: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Desk definitions
# ---------------------------------------------------------------------------

DESKS: dict[str, Desk] = {
    "momentum": Desk(
        id="momentum",
        name="Trend / Momentum Desk",
        style_prompt=(
            "Systematic trend-following on liquid crypto: SMA/EMA crossovers, "
            "Donchian breakouts, time-series momentum. Long-only, is_liquid mask. "
            "Style cue: classic CTA / AQR-like trend books (inspiration only)."
        ),
        alpha_families=("sma_cross", "ema_cross", "breakout", "ts_momentum"),
        notes="Primary family for crypto bull regimes.",
    ),
    "mean_reversion": Desk(
        id="mean_reversion",
        name="Mean-Reversion Desk",
        style_prompt=(
            "Short-horizon mean reversion on liquid names: RSI bands, Bollinger "
            "touches, z-score of returns. Long-only dips — never short. "
            "Style cue: market-neutral MR desks adapted to long-only crypto."
        ),
        alpha_families=("rsi_bands", "bollinger", "return_zscore"),
        notes="Fade oversold liquid assets only.",
    ),
    "carry_proxy": Desk(
        id="carry_proxy",
        name="Carry / Proxy Desk",
        style_prompt=(
            "Proxy carry using only Quantiacs cryptodaily fields (no external "
            "funding rates): volume persistence, volatility-risk premia proxies, "
            "relative strength vs liquid universe. Style cue: relative-value books."
        ),
        alpha_families=("vol_premia_proxy", "volume_persistence", "rel_strength"),
        notes="Only Quantiacs-provided fields; no external carry data.",
    ),
    "risk_parity": Desk(
        id="risk_parity",
        name="Risk-Parity / Vol-Target Desk",
        style_prompt=(
            "Volatility-scaled trend: inverse-vol weights, ATR scaling, target "
            "vol overlays on directional signals. Style cue: risk-parity / "
            "vol-targeting desks (Two Sigma / Point72-inspired framing only)."
        ),
        alpha_families=("inv_vol_trend", "atr_scaled", "vol_target"),
        notes="Scale positions by realized volatility.",
    ),
    "microstructure": Desk(
        id="microstructure",
        name="Crypto Microstructure Desk",
        style_prompt=(
            "Liquidity-aware signals from OHLCV only: volume spikes, range "
            "compression/expansion, high-low efficiency. Style cue: crypto "
            "prop (Cumberland / DRW-inspired framing only). Quantiacs fields only."
        ),
        alpha_families=("volume_spike", "range_break", "efficiency_ratio"),
        notes="No order-book data — cryptodaily OHLCV + is_liquid only.",
    ),
    "ensemble": Desk(
        id="ensemble",
        name="Multi-Factor Ensemble Desk",
        style_prompt=(
            "Combine orthogonal families (trend + MR + vol-scale) with equal "
            "or Sharpe-weighted blend of long-only liquid signals. "
            "Style cue: WorldQuant-style multi-alpha combination (inspiration)."
        ),
        alpha_families=("equal_blend", "signal_intersection", "rank_blend"),
        notes="Compose from existing family signals.",
    ),
}


def list_desks() -> list[Desk]:
    return list(DESKS.values())


def get_desk(desk_id: str) -> Desk:
    if desk_id not in DESKS:
        raise KeyError(f"Unknown desk: {desk_id}. Known: {sorted(DESKS)}")
    return DESKS[desk_id]


def propose_specs(desk_id: str) -> list[IdeaSpec]:
    """Deterministic seed proposals for a desk (no LLM)."""
    desk = get_desk(desk_id)
    specs: list[IdeaSpec] = []

    if desk_id == "momentum":
        specs.append(
            IdeaSpec(
                name="sma_breakout_liquid",
                desk_id=desk_id,
                family="sma_cross",
                thesis="Fast/slow SMA crossover on liquid crypto; long when fast > slow.",
                params={"sma_fast": 15, "sma_slow": 34},
                param_ranges={"sma_fast": (5, 30), "sma_slow": (20, 100)},
                tags=["trend", "baseline"],
            )
        )
        specs.append(
            IdeaSpec(
                name="donchian_breakout",
                desk_id=desk_id,
                family="breakout",
                thesis="Enter long when close breaks N-day high among liquid names.",
                params={"breakout_lookback": 20, "exit_lookback": 10},
                param_ranges={"breakout_lookback": (10, 60), "exit_lookback": (5, 30)},
                tags=["breakout"],
            )
        )
    elif desk_id == "mean_reversion":
        specs.append(
            IdeaSpec(
                name="rsi_oversold_long",
                desk_id=desk_id,
                family="rsi_bands",
                thesis="Long liquid assets when RSI is oversold; exit when RSI recovers.",
                params={"rsi_period": 14, "rsi_low": 30, "rsi_high": 70},
                param_ranges={"rsi_period": (7, 21), "rsi_low": (20, 40), "rsi_high": (60, 80)},
                tags=["mean_reversion"],
            )
        )
        specs.append(
            IdeaSpec(
                name="bollinger_touch_long",
                desk_id=desk_id,
                family="bollinger",
                thesis="Long when close touches lower Bollinger band (liquid only).",
                params={"bb_period": 20, "bb_std": 2.0},
                param_ranges={"bb_period": (10, 40), "bb_std": (1.5, 3.0)},
                tags=["mean_reversion", "bollinger"],
            )
        )
    elif desk_id == "risk_parity":
        specs.append(
            IdeaSpec(
                name="vol_scaled_sma",
                desk_id=desk_id,
                family="inv_vol_trend",
                thesis="SMA trend signal scaled by inverse realized volatility.",
                params={"sma_fast": 20, "sma_slow": 50, "vol_lookback": 20},
                param_ranges={
                    "sma_fast": (10, 40),
                    "sma_slow": (30, 120),
                    "vol_lookback": (10, 60),
                },
                tags=["vol_target", "trend"],
            )
        )
    elif desk_id == "carry_proxy":
        specs.append(
            IdeaSpec(
                name="rel_strength_liquid",
                desk_id=desk_id,
                family="rel_strength",
                thesis="Long liquid names with strongest N-day relative returns.",
                params={"mom_lookback": 30, "top_k": 5},
                param_ranges={"mom_lookback": (10, 90), "top_k": (3, 10)},
                tags=["relative_strength"],
            )
        )
    elif desk_id == "microstructure":
        specs.append(
            IdeaSpec(
                name="volume_spike_trend",
                desk_id=desk_id,
                family="volume_spike",
                thesis="Confirm SMA trend with volume above its moving average.",
                params={"sma_fast": 15, "sma_slow": 34, "vol_ma": 20},
                param_ranges={
                    "sma_fast": (5, 25),
                    "sma_slow": (20, 80),
                    "vol_ma": (10, 40),
                },
                tags=["volume", "trend"],
            )
        )
    elif desk_id == "ensemble":
        specs.append(
            IdeaSpec(
                name="sma_rsi_intersection",
                desk_id=desk_id,
                family="signal_intersection",
                thesis="Official-guide style: SMA cross AND RSI band filter (liquid).",
                params={
                    "sma_fast": 15,
                    "sma_slow": 34,
                    "rsi_period": 14,
                    "rsi_low": 34,
                    "rsi_high": 68,
                },
                param_ranges={
                    "sma_fast": (5, 30),
                    "sma_slow": (20, 100),
                    "rsi_period": (7, 21),
                    "rsi_low": (20, 45),
                    "rsi_high": (55, 80),
                },
                tags=["ensemble", "official_pattern"],
            )
        )

    # Attach desk default template
    for s in specs:
        s.template_id = desk.default_template
    return specs


def propose_all() -> list[IdeaSpec]:
    out: list[IdeaSpec] = []
    for desk_id in DESKS:
        out.extend(propose_specs(desk_id))
    return out

# Expanded mechanism catalog lives in factory/mechanisms.py
# Dual-track metadata lives in factory/tracks.py

