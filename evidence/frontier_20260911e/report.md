# Frontier benchmark

Development research ranking, not contest qualification or a live forecast.

| Rank | Candidate | Mode | Worst fold/cost SR | Research SR @12% | Dev SR @12% | Worst DD @12% | Status |
|---:|---|---|---:|---:|---:|---:|---|
| 1 | upside_response_convexity_falsifier | falsifier | 0.985 | 1.239 | 0.985 | -33.5% | COMPLETE |
| 2 | upside_response_convexity_w42 | base | 0.827 | 1.325 | 0.827 | -23.9% | COMPLETE |
| 3 | upside_response_convexity_w63 | base | 0.725 | 0.941 | 0.725 | -34.1% | COMPLETE |
| 4 | persistent_low_vol | control | 0.641 | 1.495 | 0.641 | -93.3% | COMPLETE |
| 5 | upside_response_convexity_w84 | base | 0.639 | 0.639 | 0.879 | -30.7% | COMPLETE |
| 6 | downside_impact_relief_w42 | base | 0.296 | 1.767 | 0.296 | -54.8% | COMPLETE |
| 7 | equal_liquid | control | 0.270 | 1.436 | 0.270 | -93.6% | COMPLETE |
| 8 | upside_response_convexity_ablation | ablation | 0.224 | 1.530 | 0.224 | -56.5% | COMPLETE |
| 9 | downside_impact_relief_ablation | ablation | 0.164 | 1.596 | 0.164 | -48.4% | COMPLETE |
| 10 | range_acceptance_escape_w84 | base | 0.154 | 1.612 | 0.154 | -30.7% | COMPLETE |
| 11 | range_acceptance_escape_ablation | ablation | 0.113 | 1.568 | 0.113 | -50.7% | COMPLETE |
| 12 | range_acceptance_escape_w42 | base | 0.109 | 1.737 | 0.109 | -32.0% | COMPLETE |
| 13 | range_acceptance_escape_falsifier | falsifier | 0.089 | 1.628 | 0.089 | -30.6% | COMPLETE |
| 14 | range_acceptance_escape_w63 | base | 0.085 | 1.676 | 0.085 | -30.7% | COMPLETE |
| 15 | inverse_vol_trend | control | 0.053 | 1.528 | 0.053 | -87.1% | COMPLETE |
| 16 | downside_impact_relief_w84 | base | -0.032 | 1.706 | -0.032 | -70.9% | COMPLETE |
| 17 | downside_impact_relief_w63 | base | -0.222 | 1.700 | -0.222 | -70.3% | COMPLETE |
| 18 | downside_impact_relief_falsifier | falsifier | -0.289 | 1.861 | -0.289 | -62.8% | COMPLETE |

Quantiacs local access mode: public_default.
Public/default access is sufficient for local market-data research; it is not account-bound uniqueness clearance.

### Family adjudication

| Family rank | Family | Best score | Valid cells | Action | Decision code | Reason |
|---:|---|---:|---:|---|---|---|
| 3 | downside_impact_relief | 0.296 | 5/5 | FREEZE | FALSIFIED_DEVELOPMENT | destructive control/ablation matches or beats its valid parent |
| 2 | range_acceptance_escape | 0.154 | 5/5 | FREEZE | FALSIFIED_DEVELOPMENT | destructive control/ablation matches or beats its valid parent |
| 1 | upside_response_convexity | 0.827 | 5/5 | FREEZE | FALSIFIED_DEVELOPMENT | destructive control/ablation matches or beats its valid parent |

A failed implementation cell does **not** freeze an otherwise independent preregistered family.
Falsification is economic: a valid destructive control matching/beating its valid parent, or a predefined weak-alpha floor.
Validation, diagnostic, full-IS eligibility, hosted multipass and uniqueness remain PENDING.
Historical roster metrics are not mixed into this development ranking.
