# PM report — frontier_20260910b

Status: **PENDING measured development benchmark**

This campaign was preregistered before performance inspection. It implements three distinct families:

- `topology_migration`
- `liquidity_hysteresis`
- `shock_recovery_surface`

Selection may use only the configured research (2016–2020) and development (2021–2022) folds. Validation (2023–2024) is a later promotion check and must not drive mutation. Previously inspected 2025+ periods remain diagnostic, not pristine holdout evidence. The contest live period is untouched.

## Required measured output

After the public/default Quantiacs run, record:

- Sharpe across research/dev and the 0.00 / 0.04 / 0.08 / 0.12 ATR-cost ladder;
- mean return, volatility, max drawdown, equity growth and average turnover;
- derived CAGR, Sortino and Calmar from the 0.04-cost daily return stream;
- prefix causality and bounded replay;
- cleaner/liquidity/long-only/cap invariants;
- canonical ablation and destructive-falsifier outcomes;
- residual Sharpe and correlations versus executable controls;
- family decision: `FREEZE`, `NEEDS_FORWARD_EVIDENCE`, or `PENDING`.

No metric belongs here until it is observed from the exact committed code and manifest.
