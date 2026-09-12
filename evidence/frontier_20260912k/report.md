# Frontier-K measured development evidence

**Decision: promote zero; freeze all three tested families.** All 18 declared objects completed exact public/default Quantiacs evaluation. No 2023–2024 validation, 2025+ diagnostic, live window, or account-bound uniqueness check was opened. The 2023–2024 fold remains spent and was excluded from selection.

Frontier-K activated three previously unmeasured reserves rather than retuning Frontier-J: local nearest-peer detachment under a majority-breadth state, top-two residual eigenspace rotation, and non-graph cohort residual divergence.

| Candidate | Mode | Robust SR | Research SR @12% | Dev SR @12% | Worst DD @12% |
|---|---|---:|---:|---:|---:|
| `nearest_peer_detachment_w63` | base | **0.782** | 0.782 | 0.865 | -64.9% |
| `nearest_peer_detachment_ablation` | ablation | 0.701 | 1.141 | 0.701 | -73.4% |
| `nearest_peer_detachment_falsifier` | falsifier | 0.699 | 0.793 | 0.699 | -63.4% |
| `persistent_low_vol` | control | 0.641 | 1.495 | 0.641 | -93.3% |
| `nearest_peer_detachment_w42` | base | 0.538 | 0.538 | 0.657 | -72.3% |
| `subspace_rotation_opportunity_falsifier` | falsifier | 0.415 | 1.434 | 0.415 | -89.2% |
| `subspace_rotation_opportunity_w42` | base | 0.354 | 1.412 | 0.354 | -89.4% |
| `subspace_rotation_opportunity_w63` | base | 0.332 | 1.415 | 0.332 | -89.7% |
| `equal_liquid` | control | 0.270 | 1.436 | 0.270 | -93.6% |
| `cohort_residual_divergence_ablation` | ablation | 0.241 | 0.627 | 0.241 | -86.9% |
| `subspace_rotation_opportunity_w84` | base | 0.222 | 1.492 | 0.222 | -88.9% |
| `cohort_residual_divergence_w63` | base | 0.131 | 0.455 | 0.131 | -75.1% |
| `nearest_peer_detachment_w84` | base | 0.106 | 0.995 | 0.106 | -72.9% |
| `inverse_vol_trend` | control | 0.053 | 1.528 | 0.053 | -87.1% |
| `subspace_rotation_opportunity_ablation` | ablation | 0.006 | 0.993 | 0.006 | -84.8% |
| `cohort_residual_divergence_w84` | base | -0.004 | 0.519 | -0.004 | -75.1% |
| `cohort_residual_divergence_falsifier` | falsifier | -0.063 | 0.438 | -0.063 | -75.9% |
| `cohort_residual_divergence_w42` | base | -0.091 | 0.692 | -0.091 | -67.0% |

## What we learned

**Nearest-peer detachment — KILL_WEAK_ALPHA.** The central 63-day base scored 0.782 robust Sharpe and beat both the current-low-peer ablation (0.701) and identity-rotation falsifier (0.699). Local-control residual Sharpe was 1.027 with only 0.616 correlation to equal-liquid, so this is not just the market. It still missed the fixed 1.0 robust-development floor. Preserve the formula. Do not widen the grid or promote the residual diagnostic.

**Subspace-rotation opportunity — FALSIFIED_DEVELOPMENT.** The eigenspace-rotation state beat its eigenvalue-only ablation (central 0.332 vs 0.006), but rotating residual-trend identities while keeping the same global state scored 0.415. The ranking object is not the rotation it claims. Research Sharpes above 1.4 collapsed in 2021–2022. Do not invert or retune.

**Cohort residual divergence — FALSIFIED_DEVELOPMENT.** The central 63-day divergence overlay scored 0.131 versus 0.241 for plain positive residual trend. Adding cohort-path divergence made the book worse. The 1.943 local residual Sharpe is a cash/control diagnostic on a weak book, not a promotion.

No base window reached 1.0. No later chronological window was opened.

## Research implication

After A–K, three topology-adjacent reserves that were supposed to be different from unsigned centrality migration have now been measured and frozen. Local peer detachment is the only K family whose causal controls lost, and it is still too weak. Spent 2023–2024 validation must not be reused for mutation. The next look should change the research object or bring executable incumbent controls into this harness, not retune K.

## Provenance

- measured committed head: `8e2e4bb0361e827c5a72137fd95265dc07ad2e25`
- run id: `9f60725e9ce55335108b`
- data sha256: `8bf943c40074d4107cb63edda99a7b0b268ac8ed0080fcf6de04d871ad21cd09`
- manifest sha256: `1cc60ec86a3e2cb792847f7deb8799d0bbe2f52c15e997f39b77f768c105dabd`
- Quantiacs access: `public_default`
