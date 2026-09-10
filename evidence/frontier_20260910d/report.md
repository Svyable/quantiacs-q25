# Frontier benchmark

Development research ranking, not contest qualification or a live forecast.

| Rank | Candidate | Mode | Worst fold/cost SR | Research SR @12% | Dev SR @12% | Worst DD @12% | Status |
|---:|---|---|---:|---:|---:|---:|---|
| 1 | persistent_low_vol | control | 0.641 | 1.495 | 0.641 | -93.3% | COMPLETE |
| 2 | variance_ratio_reversal_falsifier | falsifier | 0.478 | 0.478 | 0.926 | -59.1% | COMPLETE |
| 3 | equal_liquid | control | 0.270 | 1.436 | 0.270 | -93.6% | COMPLETE |
| 4 | variance_ratio_reversal_ablation | ablation | 0.158 | 1.274 | 0.158 | -81.8% | COMPLETE |
| 5 | rank_transition_w84 | base | 0.144 | 1.459 | 0.144 | -78.7% | COMPLETE |
| 6 | rank_transition_w42 | base | 0.110 | 1.650 | 0.110 | -75.8% | COMPLETE |
| 7 | rank_transition_w63 | base | 0.057 | 1.592 | 0.057 | -75.7% | COMPLETE |
| 8 | rank_transition_ablation | ablation | 0.057 | 1.590 | 0.057 | -75.7% | COMPLETE |
| 9 | rank_transition_falsifier | falsifier | 0.057 | 1.589 | 0.057 | -76.4% | COMPLETE |
| 10 | inverse_vol_trend | control | 0.053 | 1.528 | 0.053 | -87.1% | COMPLETE |
| 11 | variance_ratio_reversal_w42 | base | -0.140 | 1.416 | -0.140 | -80.2% | COMPLETE |
| 12 | variance_ratio_reversal_w84 | base | -0.176 | 1.709 | -0.176 | -76.3% | COMPLETE |
| 13 | variance_ratio_reversal_w63 | base | -0.284 | 1.676 | -0.284 | -75.2% | COMPLETE |

Quantiacs local access mode: public_default.
Public/default access is sufficient for local market-data research; it is not account-bound uniqueness clearance.

### Family adjudication

| Family rank | Family | Best score | Valid cells | Action | Decision code | Reason |
|---:|---|---:|---:|---|---|---|
| 1 | rank_transition | 0.144 | 5/5 | FREEZE | FALSIFIED_DEVELOPMENT | destructive control/ablation matches or beats its valid parent |
| 2 | variance_ratio_reversal | -0.140 | 5/5 | FREEZE | FALSIFIED_DEVELOPMENT | destructive control/ablation matches or beats its valid parent |

A failed implementation cell does **not** freeze an otherwise independent preregistered family.
Falsification is economic: a valid destructive control matching/beating its valid parent, or a predefined weak-alpha floor.
Validation, diagnostic, full-IS eligibility, hosted multipass and uniqueness remain PENDING.
Historical roster metrics are not mixed into this development ranking.
