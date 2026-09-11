# Frontier benchmark

Development research ranking, not contest qualification or a live forecast.

| Rank | Candidate | Mode | Worst fold/cost SR | Research SR @12% | Dev SR @12% | Worst DD @12% | Status |
|---:|---|---|---:|---:|---:|---:|---|
| 1 | persistent_low_vol | control | 0.641 | 1.495 | 0.641 | -93.3% | COMPLETE |
| 2 | forecast_agreement_w42 | base | 0.458 | 1.064 | 0.458 | -79.5% | COMPLETE |
| 3 | equal_liquid | control | 0.270 | 1.436 | 0.270 | -93.6% | COMPLETE |
| 4 | forecast_agreement_ablation | ablation | 0.255 | 0.968 | 0.255 | -67.1% | COMPLETE |
| 5 | forecast_agreement_w63 | base | 0.213 | 1.034 | 0.213 | -73.7% | COMPLETE |
| 6 | forecast_agreement_w21 | base | 0.145 | 1.292 | 0.145 | -76.8% | COMPLETE |
| 7 | edge_uncertainty_ablation | ablation | 0.116 | 1.262 | 0.116 | -31.0% | COMPLETE |
| 8 | inverse_vol_trend | control | 0.053 | 1.528 | 0.053 | -87.1% | COMPLETE |
| 9 | cost_relative_persistence_w84 | base | -0.121 | 0.067 | -0.121 | -31.4% | COMPLETE |
| 10 | cost_relative_persistence_w42 | base | -0.127 | 0.954 | -0.127 | -22.3% | COMPLETE |
| 11 | forecast_agreement_falsifier | falsifier | -0.134 | 0.234 | -0.134 | -32.5% | COMPLETE |
| 12 | cost_relative_persistence_ablation | ablation | -0.200 | 0.034 | -0.200 | -9.2% | COMPLETE |
| 13 | edge_uncertainty_w84 | base | -0.208 | 0.532 | -0.208 | -3.1% | COMPLETE |
| 14 | edge_uncertainty_w42 | base | -0.387 | 0.492 | -0.387 | -5.5% | COMPLETE |
| 15 | cost_relative_persistence_w63 | base | -0.400 | 0.417 | -0.400 | -25.5% | COMPLETE |
| 16 | cost_relative_persistence_falsifier | falsifier | -0.432 | 0.324 | -0.432 | -30.0% | COMPLETE |
| 17 | edge_uncertainty_falsifier | falsifier | -0.552 | 0.732 | -0.552 | -4.6% | COMPLETE |
| 18 | edge_uncertainty_w63 | base | -0.568 | 0.503 | -0.568 | -3.9% | COMPLETE |

Quantiacs local access mode: public_default.
Public/default access is sufficient for local market-data research; it is not account-bound uniqueness clearance.

### Family adjudication

| Family rank | Family | Best score | Valid cells | Action | Decision code | Reason |
|---:|---|---:|---:|---|---|---|
| 2 | cost_relative_persistence | -0.121 | 5/5 | FREEZE | FALSIFIED_DEVELOPMENT | destructive control/ablation matches or beats its valid parent |
| 3 | edge_uncertainty | -0.208 | 5/5 | FREEZE | FALSIFIED_DEVELOPMENT | destructive control/ablation matches or beats its valid parent |
| 1 | forecast_agreement | 0.458 | 5/5 | FREEZE | KILL_WEAK_ALPHA | every valid base cell is below predefined development floor Sharpe 1.0 |

A failed implementation cell does **not** freeze an otherwise independent preregistered family.
Falsification is economic: a valid destructive control matching/beating its valid parent, or a predefined weak-alpha floor.
Validation, diagnostic, full-IS eligibility, hosted multipass and uniqueness remain PENDING.
Historical roster metrics are not mixed into this development ranking.
