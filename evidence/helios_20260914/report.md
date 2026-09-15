# Frontier benchmark

Development research ranking, not contest qualification or a live forecast.

| Rank | Candidate | Mode | Worst fold/cost SR | Research SR @12% | Dev SR @12% | Worst DD @12% | Status |
|---:|---|---|---:|---:|---:|---:|---|
| 1 | persistent_low_vol | control | 0.641 | 1.495 | 0.641 | -93.3% | COMPLETE |
| 2 | helios_w189 | base | 0.320 | 2.278 | 0.320 | -35.3% | COMPLETE |
| 3 | helios_misassigned_skill | falsifier | 0.302 | 2.271 | 0.302 | -35.0% | COMPLETE |
| 4 | helios_no_cost_gate | ablation | 0.294 | 2.248 | 0.294 | -36.9% | COMPLETE |
| 5 | helios_w126 | base | 0.271 | 2.245 | 0.271 | -35.4% | COMPLETE |
| 6 | equal_liquid | control | 0.270 | 1.436 | 0.270 | -93.6% | COMPLETE |
| 7 | helios_diagonal_risk | ablation | 0.263 | 2.112 | 0.263 | -46.4% | COMPLETE |
| 8 | helios_w63 | base | 0.210 | 2.214 | 0.210 | -37.2% | COMPLETE |
| 9 | helios_static | ablation | 0.175 | 2.233 | 0.175 | -38.5% | COMPLETE |
| 10 | inverse_vol_trend | control | 0.053 | 1.528 | 0.053 | -87.1% | COMPLETE |

Quantiacs local access mode: public_default.
Public/default access is sufficient for local market-data research; it is not account-bound uniqueness clearance.

### Family adjudication

| Family rank | Family | Best score | Valid cells | Action | Decision code | Reason |
|---:|---|---:|---:|---|---|---|
| 1 | helios_factor_refinement | 0.320 | 7/7 | FREEZE | FALSIFIED_DEVELOPMENT | destructive control/ablation matches or beats its valid parent |

A failed implementation cell does **not** freeze an otherwise independent preregistered family.
Falsification is economic: a valid destructive control matching/beating its valid parent, or a predefined weak-alpha floor.
Validation, diagnostic, full-IS eligibility, hosted multipass and uniqueness remain PENDING.
Historical roster metrics are not mixed into this development ranking.
