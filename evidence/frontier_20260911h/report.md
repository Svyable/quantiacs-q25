# Frontier benchmark

Development research ranking, not contest qualification or a live forecast.

| Rank | Candidate | Mode | Worst fold/cost SR | Research SR @12% | Dev SR @12% | Worst DD @12% | Status |
|---:|---|---|---:|---:|---:|---:|---|
| 1 | neighbor_identity_churn_ablation | ablation | 0.884 | 1.315 | 0.884 | -69.8% | COMPLETE |
| 2 | persistent_low_vol | control | 0.641 | 1.495 | 0.641 | -93.3% | COMPLETE |
| 3 | clustering_escape_ablation | ablation | 0.558 | 0.558 | 1.436 | -2.2% | COMPLETE |
| 4 | neighbor_identity_churn_falsifier | falsifier | 0.448 | 1.286 | 0.448 | -47.5% | COMPLETE |
| 5 | factor_loading_escape_w84 | base | 0.401 | 0.580 | 0.401 | -0.3% | COMPLETE |
| 6 | clustering_escape_w84 | base | 0.385 | 0.981 | 0.385 | -0.1% | COMPLETE |
| 7 | neighbor_identity_churn_w84 | base | 0.341 | 1.125 | 0.341 | -50.2% | COMPLETE |
| 8 | neighbor_identity_churn_w63 | base | 0.320 | 1.183 | 0.320 | -55.9% | COMPLETE |
| 9 | neighbor_identity_churn_w42 | base | 0.282 | 1.177 | 0.282 | -58.9% | COMPLETE |
| 10 | equal_liquid | control | 0.270 | 1.436 | 0.270 | -93.6% | COMPLETE |
| 11 | clustering_escape_falsifier | falsifier | 0.250 | 0.250 | 0.438 | -0.2% | COMPLETE |
| 12 | factor_loading_escape_ablation | ablation | 0.095 | 0.095 | 1.045 | -4.6% | COMPLETE |
| 13 | inverse_vol_trend | control | 0.053 | 1.528 | 0.053 | -87.1% | COMPLETE |
| 14 | factor_loading_escape_falsifier | falsifier | 0.029 | 0.029 | 0.198 | -0.5% | COMPLETE |
| 15 | clustering_escape_w63 | base | -0.065 | -0.065 | 1.493 | -0.2% | COMPLETE |
| 16 | factor_loading_escape_w63 | base | -0.096 | -0.096 | 1.600 | -0.5% | COMPLETE |
| 17 | clustering_escape_w42 | base | -0.244 | -0.244 | -0.232 | -1.6% | COMPLETE |
| 18 | factor_loading_escape_w42 | base | -0.448 | -0.448 | 0.835 | -0.8% | COMPLETE |

Quantiacs local access mode: public_default.
Public/default access is sufficient for local market-data research; it is not account-bound uniqueness clearance.

### Family adjudication

| Family rank | Family | Best score | Valid cells | Action | Decision code | Reason |
|---:|---|---:|---:|---|---|---|
| 2 | clustering_escape | 0.385 | 5/5 | FREEZE | FALSIFIED_DEVELOPMENT | destructive control/ablation matches or beats its valid parent |
| 3 | factor_loading_escape | 0.401 | 5/5 | FREEZE | FALSIFIED_DEVELOPMENT | destructive control/ablation matches or beats its valid parent |
| 1 | neighbor_identity_churn | 0.341 | 5/5 | FREEZE | FALSIFIED_DEVELOPMENT | destructive control/ablation matches or beats its valid parent |

A failed implementation cell does **not** freeze an otherwise independent preregistered family.
Falsification is economic: a valid destructive control matching/beating its valid parent, or a predefined weak-alpha floor.
Validation, diagnostic, full-IS eligibility, hosted multipass and uniqueness remain PENDING.
Historical roster metrics are not mixed into this development ranking.
