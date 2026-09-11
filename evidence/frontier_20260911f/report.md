# Frontier benchmark

Development research ranking, not contest qualification or a live forecast.

| Rank | Candidate | Mode | Worst fold/cost SR | Research SR @12% | Dev SR @12% | Worst DD @12% | Status |
|---:|---|---|---:|---:|---:|---:|---|
| 1 | weekly_payoff_posterior_ablation | ablation | 0.970 | 1.621 | 0.970 | -23.3% | COMPLETE |
| 2 | weekly_payoff_posterior_w84 | base | 0.944 | 1.445 | 0.944 | -38.1% | COMPLETE |
| 3 | weekly_payoff_posterior_w126 | base | 0.788 | 1.500 | 0.788 | -37.9% | COMPLETE |
| 4 | adaptive_expert_cash_falsifier | falsifier | 0.778 | 1.707 | 0.778 | -76.2% | COMPLETE |
| 5 | adaptive_expert_cash_w84 | base | 0.671 | 1.472 | 0.671 | -82.2% | COMPLETE |
| 6 | persistent_low_vol | control | 0.641 | 1.495 | 0.641 | -93.3% | COMPLETE |
| 7 | adaptive_expert_cash_w126 | base | 0.571 | 1.572 | 0.571 | -79.0% | COMPLETE |
| 8 | weekly_payoff_posterior_w168 | base | 0.538 | 1.153 | 0.538 | -38.3% | COMPLETE |
| 9 | adaptive_expert_cash_w168 | base | 0.461 | 1.586 | 0.461 | -76.8% | COMPLETE |
| 10 | adaptive_expert_cash_ablation | ablation | 0.444 | 1.463 | 0.444 | -77.4% | COMPLETE |
| 11 | weekly_payoff_posterior_falsifier | falsifier | 0.409 | 1.290 | 0.409 | -40.3% | COMPLETE |
| 12 | equal_liquid | control | 0.270 | 1.436 | 0.270 | -93.6% | COMPLETE |
| 13 | triangle_coherence_ablation | ablation | 0.207 | 1.354 | 0.207 | -76.3% | COMPLETE |
| 14 | inverse_vol_trend | control | 0.053 | 1.528 | 0.053 | -87.1% | COMPLETE |
| 15 | triangle_coherence_falsifier | falsifier | -0.219 | 1.000 | -0.219 | -19.0% | COMPLETE |
| 16 | triangle_coherence_w84 | base | -0.652 | 0.684 | -0.652 | -19.4% | COMPLETE |
| 17 | triangle_coherence_w63 | base | -0.683 | 0.635 | -0.683 | -20.6% | COMPLETE |
| 18 | triangle_coherence_w42 | base | -1.000 | 0.469 | -1.000 | -28.0% | COMPLETE |

Quantiacs local access mode: public_default.
Public/default access is sufficient for local market-data research; it is not account-bound uniqueness clearance.

### Family adjudication

| Family rank | Family | Best score | Valid cells | Action | Decision code | Reason |
|---:|---|---:|---:|---|---|---|
| 2 | adaptive_expert_cash | 0.671 | 5/5 | FREEZE | FALSIFIED_DEVELOPMENT | destructive control/ablation matches or beats its valid parent |
| 3 | triangle_coherence | -0.652 | 5/5 | FREEZE | FALSIFIED_DEVELOPMENT | destructive control/ablation matches or beats its valid parent |
| 1 | weekly_payoff_posterior | 0.944 | 5/5 | FREEZE | FALSIFIED_DEVELOPMENT | destructive control/ablation matches or beats its valid parent |

A failed implementation cell does **not** freeze an otherwise independent preregistered family.
Falsification is economic: a valid destructive control matching/beating its valid parent, or a predefined weak-alpha floor.
Validation, diagnostic, full-IS eligibility, hosted multipass and uniqueness remain PENDING.
Historical roster metrics are not mixed into this development ranking.
