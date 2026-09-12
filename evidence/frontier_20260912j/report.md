# Frontier-J measured development evidence

**Decision: promote zero; freeze all three tested families.** All 18 declared objects completed exact public/default Quantiacs evaluation. No 2023–2024 validation, 2025+ diagnostic, live window, or account-bound uniqueness check was opened.

Frontier-J deliberately changed the research object after Frontier-I rather than tuning `topology_migration_w84`: signed positive-edge migration, a global spectral-diversification state, and momentum after removing the leading residual principal component.

| Candidate | Mode | Robust SR | Research SR @12% | Dev SR @12% | Worst DD @12% |
|---|---|---:|---:|---:|---:|
| `positive_edge_shedding_ablation` | ablation | **0.935** | 0.935 | 1.211 | -52.0% |
| `positive_edge_shedding_falsifier` | falsifier | 0.811 | 1.010 | 0.811 | -45.1% |
| `spectral_diversification_gate_w42` | base | **0.786** | 0.786 | 1.145 | -61.1% |
| `positive_edge_shedding_w63` | base | **0.752** | 0.752 | 1.159 | -44.0% |
| `spectral_residual_momentum_w63` | base | **0.667** | 1.165 | 0.667 | -83.4% |
| `spectral_diversification_gate_ablation` | ablation | 0.665 | 1.361 | 0.665 | -79.0% |
| `persistent_low_vol` | control | 0.641 | 1.495 | 0.641 | -93.3% |
| `spectral_residual_momentum_w84` | base | 0.586 | 1.385 | 0.586 | -82.6% |
| `spectral_diversification_gate_w84` | base | 0.538 | 0.538 | 0.914 | -71.0% |
| `spectral_diversification_gate_w63` | base | 0.498 | 0.776 | 0.498 | -65.5% |
| `spectral_residual_momentum_ablation` | ablation | 0.487 | 1.319 | 0.487 | -80.0% |
| `positive_edge_shedding_w84` | base | 0.395 | 0.395 | 1.209 | -68.9% |
| `positive_edge_shedding_w42` | base | 0.314 | 0.314 | 1.681 | -61.4% |
| `equal_liquid` | control | 0.270 | 1.436 | 0.270 | -93.6% |
| `spectral_residual_momentum_falsifier` | falsifier | 0.254 | 1.122 | 0.254 | -80.1% |
| `spectral_diversification_gate_falsifier` | falsifier | 0.188 | 0.995 | 0.188 | -73.6% |
| `inverse_vol_trend` | control | 0.053 | 1.528 | 0.053 | -87.1% |
| `spectral_residual_momentum_w42` | base | -0.130 | 1.192 | -0.130 | -80.8% |

## What we learned

**Positive-edge shedding — FALSIFIED_DEVELOPMENT.** The central 63-day base scored 0.752 robust Sharpe, while the static low-positive-edge ablation scored 0.935 and the identity-rotation falsifier 0.811. The 42-day base looked excellent in the 2021–2022 dev fold (1.681 Sharpe at 12% ATR cost; local-control residual Sharpe 2.191) but only 0.314 in 2016–2020. That is a regime-sensitive result, not robust alpha. Do not tune a state detector to rescue it using these observed folds.

**Spectral-diversification gate — FALSIFIED_DEVELOPMENT.** Its best window was 42 days at 0.786 robust Sharpe, with 1.145 dev Sharpe at 12% ATR costs and 1.461 dev residual Sharpe against the three generic controls. The central 63-day gate scored 0.498 versus 0.665 for the no-gate ablation. The chosen spectral state therefore does not earn its complexity.

**Spectral residual momentum — KILL_WEAK_ALPHA.** The central PC-residualized strategy did beat its central ablation and rotated-loading falsifier, and the paired development return difference versus the falsifier was positive in the predeclared block bootstrap. But every base window remains below the fixed 1.0 robust-development floor; the best base is 0.667. This is genuine weak economics rather than allocator erasure, and it stays frozen.

The matched controls materially changed deployed capital, so these are informative economic failures rather than no-op formulas. No failed family may be inverted, threshold-tuned, or have its best control relabeled as a winner.

## Research implication

After A–J, the result is increasingly specific: generic topology levels, clustering, neighbor churn, conditional dependence, signed positive-edge decomposition, spectral opportunity gating, and PC-residual momentum have all failed to reproduce the strength of the original residual **topology migration during fragmentation** mechanism. `topology_migration_w84` remains the only new-campaign family above the internal 1.0 robust-development floor.

The highest-value next action is therefore not another development retune. It is a **frozen forward evaluation of the already-selected topology-migration family on the untouched 2023–2024 validation fold**. Parameters, controls, cost ladder and execution semantics must remain unchanged; the validation result can only increase or decrease confidence, never drive mutation.

## Provenance

- measured PR head: `e683b911d0a2ae2c04d60167008d56f5691308f8`
- workflow run: `34673938339`
- artifact: `10291064478`
- artifact digest: `sha256:77154132014707ad86066f93227ea10cfc8ffa6bbc6b5795d50fafa25747583b`
- Quantiacs access: `public_default`
- data hash: `bc932fc6f016c2bc0fbf3f51bf6f59b48d895cd1ac7ed27602d63ecbfdc8bc58`
- manifest hash: `4deba8cf8937972efa3d72e8ebc4874b4e3f2841ee7e99cae90489e174d68836`

These are repeated historical development simulations, not forecasts or contest qualification.
