# Frontier-I measured development evidence

**Decision: freeze all three tested families; promote zero.** The exact public/default Quantiacs run completed all 18 declared objects. No validation, recent diagnostic, live window, or account-bound uniqueness check was opened.

Frontier-I deliberately changed the research object after Frontier-H: two families used a shrinkage precision / partial-correlation graph rather than another 21-day change of a marginal-correlation node statistic; the third was a non-topology opportunity-density hypothesis.

| Candidate | Mode | Robust SR | Research SR @12% | Dev SR @12% | Worst DD @12% |
|---|---|---:|---:|---:|---:|
| persistent_low_vol | control | 0.641 | 1.495 | 0.641 | -93.3% |
| trend_dispersion_gate_falsifier | falsifier | 0.384 | 0.384 | 0.793 | -93.0% |
| partial_edge_entropy_w84 | base | **0.304** | 1.230 | 0.304 | -95.9% |
| conditional_decoupling_w84 | base | **0.288** | 1.239 | 0.288 | -95.5% |
| equal_liquid | control | 0.270 | 1.436 | 0.270 | -93.6% |
| trend_dispersion_gate_ablation | ablation | 0.210 | 1.479 | 0.210 | -94.7% |
| conditional_decoupling_ablation | ablation | 0.201 | 1.433 | 0.201 | -95.2% |
| conditional_decoupling_falsifier | falsifier | 0.196 | 1.452 | 0.196 | -94.6% |
| partial_edge_entropy_w42 | base | 0.172 | 1.385 | 0.172 | -94.8% |
| conditional_decoupling_w63 | base | 0.155 | 1.472 | 0.155 | -93.3% |
| partial_edge_entropy_w63 | base | 0.138 | 1.374 | 0.138 | -94.3% |
| partial_edge_entropy_falsifier | falsifier | 0.127 | 1.429 | 0.127 | -93.7% |
| partial_edge_entropy_ablation | ablation | 0.119 | 1.451 | 0.119 | -94.2% |
| inverse_vol_trend | control | 0.053 | 1.528 | 0.053 | -87.1% |
| conditional_decoupling_w42 | base | 0.013 | 1.463 | 0.013 | -93.8% |
| trend_dispersion_gate_w42 | base | -0.358 | 1.248 | -0.358 | -81.5% |
| trend_dispersion_gate_w84 | base | -0.669 | 1.279 | -0.669 | -88.6% |
| trend_dispersion_gate_w63 | base | -0.812 | 1.377 | -0.812 | -87.7% |

## Adjudication

**Conditional decoupling — FALSIFIED_DEVELOPMENT.** The best window was 84 days at 0.288 robust Sharpe. The central 63-day parent scored 0.155 versus 0.201 for the static marginal-isolation ablation and 0.196 for identity rotation. The defining conditional-decoupling direction therefore did not earn its complexity.

**Partial-edge entropy — KILL_WEAK_ALPHA.** This was the best Frontier-I base family, with the 84-day window at 0.304 robust Sharpe, but every base window remained far below the fixed 1.0 floor. The central parent changed capital versus both controls, so this is genuine weak economics rather than allocator erasure.

**Trend-dispersion gate — FALSIFIED_DEVELOPMENT.** The expansion gate was strongly harmful in development. The central 63-day parent scored -0.812 robust Sharpe; its no-gate ablation scored 0.210 and the opposite/compression gate scored 0.384. Do not invert the idea after observing this result; the family is frozen.

The matched-target diagnostics confirm the mechanisms materially changed capital: central conditional decoupling differed from its ablation on 21.1% of target days; partial-edge entropy on 14.4%; trend-dispersion gating on 53.9%. The poor results are therefore economically informative.

## Provenance

- workflow run: `34672135922`
- artifact: `10291466031`
- artifact digest: `sha256:bda7bfeab1840cc5a552b8e1b86f162f2bbd799eb1b2738dfc992c2ba1a2368e`
- access mode: `public_default`
- Quantiacs data hash: `bc932fc6f016c2bc0fbf3f51bf6f59b48d895cd1ac7ed27602d63ecbfdc8bc58`
- manifest hash: `ab42288f99a20eb0fcf5b0de913b4d0fd152c74fd6cc7e403ebeccfd067daf07`
- exact source hashes are recorded in `observed_summary.json` and the preserved Actions artifact.

This is repeated development evidence, not a fresh holdout. `topology_migration_w84` remains the only new-campaign family above the internal 1.0 robust-development floor.
