# Frontier benchmark

Development research ranking, not contest qualification or a live forecast.

| Rank | Candidate | Mode | Worst fold/cost SR | Research SR @12% | Dev SR @12% | Worst DD @12% | Status |
|---:|---|---|---:|---:|---:|---:|---|
| 1 | persistent_low_vol | control | 0.641 | 1.495 | 0.641 | -93.3% | COMPLETE |
| 2 | dollar_volume_share_migration_w42 | base | 0.614 | 1.403 | 0.614 | -65.3% | COMPLETE |
| 3 | dollar_volume_share_migration_w21 | base | 0.443 | 1.418 | 0.443 | -81.2% | COMPLETE |
| 4 | permutation_entropy_contraction_w126 | base | 0.401 | 0.992 | 0.401 | -65.1% | COMPLETE |
| 5 | dollar_volume_share_migration_ablation | ablation | 0.281 | 1.465 | 0.281 | -92.4% | COMPLETE |
| 6 | equal_liquid | control | 0.270 | 1.436 | 0.270 | -93.6% | COMPLETE |
| 7 | permutation_entropy_contraction_w63 | base | 0.241 | 0.898 | 0.241 | -76.5% | COMPLETE |
| 8 | dollar_volume_share_migration_w63 | base | 0.185 | 1.182 | 0.185 | -81.9% | COMPLETE |
| 9 | relative_value_convergence_w63 | base | 0.182 | 0.686 | 0.182 | -77.7% | COMPLETE |
| 10 | permutation_entropy_contraction_ablation | ablation | 0.166 | 1.523 | 0.166 | -92.4% | COMPLETE |
| 11 | permutation_entropy_contraction_falsifier | falsifier | 0.132 | 1.266 | 0.132 | -69.6% | COMPLETE |
| 12 | inverse_vol_trend | control | 0.053 | 1.528 | 0.053 | -87.1% | COMPLETE |
| 13 | relative_value_convergence_ablation | ablation | -0.015 | 1.099 | -0.015 | -96.1% | COMPLETE |
| 14 | relative_value_convergence_w42 | base | -0.024 | -0.024 | 0.231 | -95.8% | COMPLETE |
| 15 | permutation_entropy_contraction_w84 | base | -0.046 | 1.208 | -0.046 | -74.5% | COMPLETE |
| 16 | dollar_volume_share_migration_falsifier | falsifier | -0.201 | 1.156 | -0.201 | -73.4% | COMPLETE |
| 17 | relative_value_convergence_w21 | base | -0.397 | -0.076 | -0.397 | -95.6% | COMPLETE |
| 18 | relative_value_convergence_falsifier | falsifier | -0.471 | 1.181 | -0.471 | -87.1% | COMPLETE |

Quantiacs local access mode: public_default.
Public/default access is sufficient for local market-data research; it is not account-bound uniqueness clearance.

### Family adjudication

| Family rank | Family | Best score | Valid cells | Action | Decision code | Reason |
|---:|---|---:|---:|---|---|---|
| 1 | dollar_volume_share_migration | 0.614 | 5/5 | FREEZE | KILL_WEAK_ALPHA | every valid base cell is below predefined development floor Sharpe 1.0 |
| 2 | permutation_entropy_contraction | 0.401 | 5/5 | FREEZE | FALSIFIED_DEVELOPMENT | destructive control/ablation matches or beats its valid parent |
| 3 | relative_value_convergence | 0.182 | 5/5 | FREEZE | FALSIFIED_DEVELOPMENT | destructive control/ablation matches or beats its valid parent |

A failed implementation cell does **not** freeze an otherwise independent preregistered family.
Falsification is economic: a valid destructive control matching/beating its valid parent, or a predefined weak-alpha floor.
Validation, diagnostic, full-IS eligibility, hosted multipass and uniqueness remain PENDING.
Historical roster metrics are not mixed into this development ranking.
