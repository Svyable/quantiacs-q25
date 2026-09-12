# Topology rank stability measured development evidence

**Decision: freeze the family; promote zero.** All five preregistered cells completed under the exact public/default Quantiacs development harness, alongside the same three generic controls used elsewhere in the research program.

| Candidate | Mode | Robust SR | Research SR @12% | Dev SR @12% | Worst DD @12% |
|---|---|---:|---:|---:|---:|
| persistent_low_vol | control | 0.641 | 1.495 | 0.641 | -93.3% |
| equal_liquid | control | 0.270 | 1.436 | 0.270 | -93.6% |
| topology_rank_stability_ablation | ablation | **0.211** | 1.392 | 0.211 | -92.2% |
| inverse_vol_trend | control | 0.053 | 1.528 | 0.053 | -87.1% |
| topology_rank_stability_w42 | base | **-0.048** | 1.210 | -0.048 | -96.1% |
| topology_rank_stability_w84 | base | -0.092 | 1.318 | -0.092 | -95.0% |
| topology_rank_stability_w63 | base | -0.175 | 1.199 | -0.175 | -95.3% |
| topology_rank_stability_falsifier | falsifier | -0.176 | 1.574 | -0.176 | -94.0% |

## Adjudication

**`topology_rank_stability` — `FALSIFIED_DEVELOPMENT`.** The best declared base was the 42-day cell at robust Sharpe -0.048. The preregistered current-topology-rank ablation scored +0.211 and therefore beat every base cell. This is an economic falsification under the declared destructive-control rule, not an implementation failure.

The family also failed to add useful residual evidence against generic controls. Development residual Sharpe was -0.742 for w42, -1.112 for w63, and -1.103 for w84. Correlations to equal-liquid were approximately 0.965–0.968 for the base cells, so the proposed rank-stability conditioning did not create the intended distinct structural satellite.

Do not tune the window grid, invert the signal, or promote the ablation after observing these results. The family is frozen as negative evidence. This result does **not** alter the earlier `topology_migration_w84` development packet; that remains a separate pre-existing survivor and still requires its forward/validation boundary.

## Provenance

- workflow run: `34675022256`
- artifact: `10291802505`
- artifact digest: `sha256:e8bce2f1276e9f0ca0696c23ba88db5ca76b2ea334912ba943d22f34acaa43b4`
- access mode: `public_default`
- data hash: `bc932fc6f016c2bc0fbf3f51bf6f59b48d895cd1ac7ed27602d63ecbfdc8bc58`
- manifest hash: `8059abcd58a1e5510b3f04bdcdc56e632aa54f246ddb1201fe1f4a5738279501`
- strategy source hash: `5708214efd0f4518a79e9367738f0e1fef5290d7a047abd94df180803538ea07`

This is development evidence only. Validation, hosted multipass behavior, policy eligibility, and account-bound uniqueness clearance remain outside this packet.
