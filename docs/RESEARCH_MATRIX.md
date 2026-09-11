---
title: Research Matrix
description: Evidence-aware ranking of frozen Q25 incumbents and current development candidates.
---

# Q25 research matrix

> **Two lanes, never one fake leaderboard.** Frozen historical incumbents and current development candidates use different evidence vintages and harnesses. We rank *within* a comparable lane and show evidence quality beside strategy quality.

## Current development candidates

The development score is the **worst Sharpe across the 2016–2020 research fold and 2021–2022 dev fold at 4%, 8%, and 12% ATR-linked slippage**. That is deliberately harsher than headline full-period Sharpe.

| Dev rank | Candidate | Family | Robust SR | Research SR @12% | Dev SR @12% | Research DD @12% | Dev DD @12% | Status |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 1 | `topology_migration_w84` | topology_migration | 1.376 | 1.376 | 1.863 | -46.3% | -26.7% | COMPLETE |
| 2 | `topology_migration_w63` | topology_migration | 1.080 | 1.205 | 1.080 | -51.1% | -53.4% | COMPLETE |
| 3 | `liquidity_hysteresis_w21` | liquidity_hysteresis | 0.333 | 1.062 | 0.333 | -52.0% | -51.8% | COMPLETE |
| 4 | `liquidity_hysteresis_w42` | liquidity_hysteresis | 0.333 | 1.062 | 0.333 | -52.0% | -51.8% | COMPLETE |
| 5 | `liquidity_hysteresis_w63` | liquidity_hysteresis | 0.333 | 1.062 | 0.333 | -52.0% | -51.8% | COMPLETE |
| — | `shock_recovery_surface_w28` | shock_recovery_surface | — | — | — | — | — | FAILED |
| — | `shock_recovery_surface_w42` | shock_recovery_surface | — | — | — | — | — | FAILED |
| — | `shock_recovery_surface_w56` | shock_recovery_surface | — | — | — | — | — | FAILED |
| — | `topology_migration_w42` | topology_migration | — | — | — | — | — | FAILED |

**Read-through:** topology migration is the only Frontier-B base family with valid cells above the internal 1.0 development floor. `topology_migration_w84` is the strongest observed cell, but it is still development evidence: drawdown is material, one neighboring grid cell failed integrity, and validation / recent diagnostics / current uniqueness are untouched.

Liquidity hysteresis is currently a useful state variable, not a standalone alpha candidate: all three valid windows collapse to the same weak robust score. Shock-recovery base cells are not economically adjudicated because their implementation/integrity checks failed in this artifact.

## Controls and destructive tests

| Object | Type | Robust SR | Research SR @12% | Dev SR @12% | Purpose |
|---|---|---:|---:|---:|---|
| `persistent_low_vol` | control | 0.641 | 1.495 | 0.641 | low-novelty economic control |
| `liquidity_hysteresis_ablation` | ablation | 0.143 | 1.747 | 0.143 | remove hysteresis distinction |
| `liquidity_hysteresis_falsifier` | falsifier | 0.245 | 1.732 | 0.245 | flip lifecycle premise |
| `shock_recovery_surface_falsifier` | falsifier | 0.359 | 1.069 | 0.359 | destroy recovery premise |
| `topology_migration_ablation` | ablation | 1.009 | 1.009 | 1.025 | remove migration component |
| `topology_migration_falsifier` | falsifier | 0.387 | 0.387 | 0.779 | destroy topology assignment |

## Frozen historical incumbents

These rows are the dated August-2026 research roster. They are not silently recomputed or cross-ranked against Frontier-B development scores.

| Frozen rank | Strategy | Role | Full SR | Stress SR | Max DD | Evidence status |
|---:|---|---|---:|---:|---:|---|
| 1 | **V10 multi-factor ensemble — Pareto** | primary legacy core | 2.261 | 1.965 @ 12% ATR | -30.9% | prepare_precheck |
| 2 | **V11 new-only event ensemble — Balanced** | orthogonal event / lifecycle core | 1.261 | 0.899 @ 12% ATR | -23.1% | prepare_precheck |
| 3 | **C165 mobility / consensus risk** | risk-efficiency core | 1.230 | 0.934 @ 12% ATR | -21.4% | prepare_precheck |
| 4 | **V12 signed volume diffusion — 50/50 bridge** | structural volume/return network core | 1.035 | 0.750 @ 12% ATR | -33.9% | prepare_precheck_exact_official_gate_required |
| 5 | **Co-crash shelter — base 126D** | defensive crash-comovement sleeve | 1.772 | 1.627 @ 12% ATR | -14.4% | prepare_precheck |
| 6 | **Residual dispersion switch** | sparse dispersion-conditioned residual sleeve | 1.536 | 1.410 @ 8% ATR | -12.0% | prepare_precheck |
| 7 | **Breadth Thrust Switch** | market breadth acceleration timing | 1.185 | 1.075 @ 8% ATR | -21.5% | prepare_precheck |
| 8 | **Slow defensive factor balance** | multi-factor defensive balance | 1.526 | 1.445 @ 8% ATR | -24.7% | prepare_precheck |
| 9 | **126D positive-return consistency — five names** | persistent trend reserve | 1.700 | 1.538 @ 12% ATR | -24.8% | conditional_reserve |
| 10 | **V5 latency ensemble** | low-risk alternative within the V10 family | 2.105 | 1.830 @ 12% ATR | -10.3% | conditional_reserve_high_overlap_with_v10 |

## Evidence health

Frontier-B observed artifact: workflow run **34437464861**, artifact **10136721138**, Quantiacs access **`public_default`**, data hash `bc932fc6f016c2bc…`.

The artifact contains **11 completed cells** and **7 failed cells**. Failed cells stay visible. A software/integrity failure is not converted into a bad Sharpe, and it does not automatically falsify every other preregistered cell in the mechanism family.

The next harness version emits a candidate packet for every attempted cell with strategy quality, evidence completeness, implementation health, cost ladder, CAGR/Sortino/Calmar, drawdown, turnover, causality and provenance. Missing fields remain missing; they are never imputed to make a matrix look complete.

[Back to Quant Lab](index.md) · [Evidence model](EVIDENCE_MODEL.md) · [Strategy atlas](STRATEGY_ATLAS.md) · [Testing pyramid](TESTING_PYRAMID.md)

### Invalid cells retained for repair

| Cell | Family | Failure |
|---|---|---|
| `equal_liquid` | control | AssertionError |
| `inverse_vol_trend` | control | AssertionError |
| `shock_recovery_surface_ablation` | shock_recovery_surface | AssertionError |
| `shock_recovery_surface_w28` | shock_recovery_surface | AssertionError |
| `shock_recovery_surface_w42` | shock_recovery_surface | AssertionError |
| `shock_recovery_surface_w56` | shock_recovery_surface | AssertionError |
| `topology_migration_w42` | topology_migration | AssertionError |

## frontier_20260910d: separate development campaign

Exact local measurements; no automatic promotion or cross-campaign ranking.

| Candidate | Mode | Worst fold/cost SR | Worst DD @12% | Status |
|---|---|---:|---:|---|
| `persistent_low_vol` | control | 0.641 | -93.3% | COMPLETE |
| `variance_ratio_reversal_falsifier` | falsifier | 0.478 | -59.1% | COMPLETE |
| `equal_liquid` | control | 0.270 | -93.6% | COMPLETE |
| `variance_ratio_reversal_ablation` | ablation | 0.158 | -81.8% | COMPLETE |
| `rank_transition_w84` | base | 0.144 | -78.7% | COMPLETE |
| `rank_transition_w42` | base | 0.110 | -75.8% | COMPLETE |
| `rank_transition_w63` | base | 0.057 | -75.7% | COMPLETE |
| `rank_transition_ablation` | ablation | 0.057 | -75.7% | COMPLETE |
| `rank_transition_falsifier` | falsifier | 0.057 | -76.4% | COMPLETE |
| `inverse_vol_trend` | control | 0.053 | -87.1% | COMPLETE |
| `variance_ratio_reversal_w42` | base | -0.140 | -80.2% | COMPLETE |
| `variance_ratio_reversal_w84` | base | -0.176 | -76.3% | COMPLETE |
| `variance_ratio_reversal_w63` | base | -0.284 | -75.2% | COMPLETE |

| Family | Decision | Reason |
|---|---|---|
| rank_transition | FALSIFIED_DEVELOPMENT | destructive control/ablation matches or beats its valid parent |
| variance_ratio_reversal | FALSIFIED_DEVELOPMENT | destructive control/ablation matches or beats its valid parent |

[Evidence packet](../evidence/frontier_20260910d/report.md) · [Research report](../experiments/frontier_20260910d/pm_report.md)

## frontier_20260911e: separate development campaign

Exact local measurements; no automatic promotion or cross-campaign ranking.

| Candidate | Mode | Worst fold/cost SR | Worst DD @12% | Status |
|---|---|---:|---:|---|
| `upside_response_convexity_falsifier` | falsifier | 0.985 | -33.5% | COMPLETE |
| `upside_response_convexity_w42` | base | 0.827 | -23.9% | COMPLETE |
| `upside_response_convexity_w63` | base | 0.725 | -34.1% | COMPLETE |
| `persistent_low_vol` | control | 0.641 | -93.3% | COMPLETE |
| `upside_response_convexity_w84` | base | 0.639 | -30.7% | COMPLETE |
| `downside_impact_relief_w42` | base | 0.296 | -54.8% | COMPLETE |
| `equal_liquid` | control | 0.270 | -93.6% | COMPLETE |
| `upside_response_convexity_ablation` | ablation | 0.224 | -56.5% | COMPLETE |
| `downside_impact_relief_ablation` | ablation | 0.164 | -48.4% | COMPLETE |
| `range_acceptance_escape_w84` | base | 0.154 | -30.7% | COMPLETE |
| `range_acceptance_escape_ablation` | ablation | 0.113 | -50.7% | COMPLETE |
| `range_acceptance_escape_w42` | base | 0.109 | -32.0% | COMPLETE |
| `range_acceptance_escape_falsifier` | falsifier | 0.089 | -30.6% | COMPLETE |
| `range_acceptance_escape_w63` | base | 0.085 | -30.7% | COMPLETE |
| `inverse_vol_trend` | control | 0.053 | -87.1% | COMPLETE |
| `downside_impact_relief_w84` | base | -0.032 | -70.9% | COMPLETE |
| `downside_impact_relief_w63` | base | -0.222 | -70.3% | COMPLETE |
| `downside_impact_relief_falsifier` | falsifier | -0.289 | -62.8% | COMPLETE |

| Family | Decision | Reason |
|---|---|---|
| downside_impact_relief | FALSIFIED_DEVELOPMENT | destructive control/ablation matches or beats its valid parent |
| range_acceptance_escape | FALSIFIED_DEVELOPMENT | destructive control/ablation matches or beats its valid parent |
| upside_response_convexity | FALSIFIED_DEVELOPMENT | destructive control/ablation matches or beats its valid parent |

[Evidence packet](../evidence/frontier_20260911e/report.md) · [Research report](../experiments/frontier_20260911e/pm_report.md)

## frontier_20260911f: separate development campaign

Exact local measurements; no automatic promotion or cross-campaign ranking.

| Candidate | Mode | Worst fold/cost SR | Worst DD @12% | Status |
|---|---|---:|---:|---|
| `weekly_payoff_posterior_ablation` | ablation | 0.970 | -23.3% | COMPLETE |
| `weekly_payoff_posterior_w84` | base | 0.944 | -38.1% | COMPLETE |
| `weekly_payoff_posterior_w126` | base | 0.788 | -37.9% | COMPLETE |
| `adaptive_expert_cash_falsifier` | falsifier | 0.778 | -76.2% | COMPLETE |
| `adaptive_expert_cash_w84` | base | 0.671 | -82.2% | COMPLETE |
| `persistent_low_vol` | control | 0.641 | -93.3% | COMPLETE |
| `adaptive_expert_cash_w126` | base | 0.571 | -79.0% | COMPLETE |
| `weekly_payoff_posterior_w168` | base | 0.538 | -38.3% | COMPLETE |
| `adaptive_expert_cash_w168` | base | 0.461 | -76.8% | COMPLETE |
| `adaptive_expert_cash_ablation` | ablation | 0.444 | -77.4% | COMPLETE |
| `weekly_payoff_posterior_falsifier` | falsifier | 0.409 | -40.3% | COMPLETE |
| `equal_liquid` | control | 0.270 | -93.6% | COMPLETE |
| `triangle_coherence_ablation` | ablation | 0.207 | -76.3% | COMPLETE |
| `inverse_vol_trend` | control | 0.053 | -87.1% | COMPLETE |
| `triangle_coherence_falsifier` | falsifier | -0.219 | -19.0% | COMPLETE |
| `triangle_coherence_w84` | base | -0.652 | -19.4% | COMPLETE |
| `triangle_coherence_w63` | base | -0.683 | -20.6% | COMPLETE |
| `triangle_coherence_w42` | base | -1.000 | -28.0% | COMPLETE |

| Family | Decision | Reason |
|---|---|---|
| adaptive_expert_cash | FALSIFIED_DEVELOPMENT | destructive control/ablation matches or beats its valid parent |
| triangle_coherence | FALSIFIED_DEVELOPMENT | destructive control/ablation matches or beats its valid parent |
| weekly_payoff_posterior | FALSIFIED_DEVELOPMENT | destructive control/ablation matches or beats its valid parent |

[Evidence packet](../evidence/frontier_20260911f/report.md) · [Research report](../experiments/frontier_20260911f/pm_report.md)
