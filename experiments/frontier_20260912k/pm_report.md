# Frontier-K: nearest-peer detachment, subspace rotation, cohort divergence

**Decision: freeze all three tested families; promote zero.** All 18 objects completed exact public/default Quantiacs evaluation on the reused 2016–2020 / 2021–2022 development surface. The spent 2023–2024 fold was excluded. No live window or account-bound uniqueness check was opened.

Frontier-K did not invent new hypotheses after seeing I/J returns. It activated three reserves that were preregistered before their own market looks.

## Frozen hypotheses

| Approach | Mechanism | Ablation | Destructive control |
|---|---|---|---|
| Nearest-peer detachment | Broad local-detachment state when a majority of eligibles lose strength to their single strongest residual peer; rank positive-residual names by own detachment | Current low strongest-peer correlation under the same breadth state | Rotate asset-level detachment, keep the breadth state |
| Subspace-rotation opportunity | Residual-eigenspace principal-angle rotation as a deployment state over positive residual trend | Leading-eigenvalue concentration change only | Rotate positive residual-trend scores, keep the global rotation state |
| Cohort residual divergence | Positive-trend leaders whose path diverges from the contemporaneous trend cohort (non-graph) | Plain positive residual trend | Prefer cohort-conforming leaders instead of divergent ones |

## Exact development results

Robust Sharpe is the minimum across 2016–2020 research and 2021–2022 development at 4%, 8% and 12% ATR-linked slippage.

| Cell | Mode | Robust SR | Research SR, 12% | Dev SR, 12% | Worst DD, 12% |
|---|---|---:|---:|---:|---:|
| nearest_peer_detachment_w63 | base | 0.782 | 0.782 | 0.865 | -64.9% |
| nearest_peer_detachment_ablation | ablation | 0.701 | 1.141 | 0.701 | -73.4% |
| nearest_peer_detachment_falsifier | falsifier | 0.699 | 0.793 | 0.699 | -63.4% |
| persistent_low_vol | control | 0.641 | 1.495 | 0.641 | -93.3% |
| nearest_peer_detachment_w42 | base | 0.538 | 0.538 | 0.657 | -72.3% |
| subspace_rotation_opportunity_falsifier | falsifier | 0.415 | 1.434 | 0.415 | -89.2% |
| subspace_rotation_opportunity_w42 | base | 0.354 | 1.412 | 0.354 | -89.4% |
| subspace_rotation_opportunity_w63 | base | 0.332 | 1.415 | 0.332 | -89.7% |
| equal_liquid | control | 0.270 | 1.436 | 0.270 | -93.6% |
| cohort_residual_divergence_ablation | ablation | 0.241 | 0.627 | 0.241 | -86.9% |
| subspace_rotation_opportunity_w84 | base | 0.222 | 1.492 | 0.222 | -88.9% |
| cohort_residual_divergence_w63 | base | 0.131 | 0.455 | 0.131 | -75.1% |
| nearest_peer_detachment_w84 | base | 0.106 | 0.995 | 0.106 | -72.9% |
| inverse_vol_trend | control | 0.053 | 1.528 | 0.053 | -87.1% |
| subspace_rotation_opportunity_ablation | ablation | 0.006 | 0.993 | 0.006 | -84.8% |
| cohort_residual_divergence_w84 | base | -0.004 | 0.519 | -0.004 | -75.1% |
| cohort_residual_divergence_falsifier | falsifier | -0.063 | 0.438 | -0.063 | -75.9% |
| cohort_residual_divergence_w42 | base | -0.091 | 0.692 | -0.091 | -67.0% |

## Adjudication

**Nearest-peer detachment — KILL_WEAK_ALPHA.** The central 63-day base scored 0.782 and beat both the static-isolation ablation (0.701) and identity rotation (0.699). The defining transform therefore changed capital in the claimed direction. Every base window still missed the fixed 1.0 robust-development floor. Do not widen the grid or promote the 0.782 cell.

**Subspace-rotation opportunity — FALSIFIED_DEVELOPMENT.** The best base was 0.354 (42-day). The central 63-day parent scored 0.332 versus 0.415 for shuffled residual-trend labels under the same rotation state. The global rotation state did not earn an identity-specific book.

**Cohort residual divergence — FALSIFIED_DEVELOPMENT.** The central 63-day parent scored 0.131 versus 0.241 for plain positive residual trend. Preferring divergent leaders was worse than the no-divergence ablation. Do not invert to “prefer conforming leaders” after seeing this result.

No base window reached 1.0. The spent 2023–2024 fold was not reopened. `topology_migration_w84` already failed its frozen forward gate at 0.314 SR@12%; this packet does not restore that family.

## Next research boundary

Stop mining 21-day changes of residual-correlation node statistics. The remaining unmeasured seam from Frontier-B is **shock-recovery**, whose base cells failed integrity and were never economically adjudicated. New work should be a non-graph path/recovery or execution-density object, preregistered on 2016–2022 only.

## Reproduce

```bash
API_KEY=default python -m research.iteration \
  --manifest experiments/frontier_20260912k/manifest.json \
  --output results/frontier_20260912k --budget 18
python -m pytest -q tests
python scripts/build_research_dashboard.py --check
python scripts/build_methodology_health.py --check
```
