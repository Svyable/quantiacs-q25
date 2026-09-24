# VCB × breadth sparse-trigger execution — preregistration

Status: FROZEN BEFORE ECONOMIC OBSERVATION
Date: 2026-09-24
Parent evidence: `research/evidence/vcb_breadth_turnover_ensemble_20260924.md`

## Hypothesis

The rejected 2%-absolute per-asset no-trade band reduced turnover only 6.8075%, so a different execution mechanism is required rather than threshold rescue. A sparse portfolio-level rebalance trigger may remove small, distributed target changes while retaining the static 50/50 VCB × breadth-dispersion ensemble's cross-sectional information.

## Frozen mechanism

1. Compute the existing causal static 50/50 VCB × breadth-dispersion target with the same Sponsor `is_liquid` top-10 monthly universe and all existing long-only/gross constraints.
2. Mandatory eligibility exits always execute immediately: any asset leaving the permitted liquid universe is forced to zero.
3. Otherwise compute portfolio target displacement as `0.5 * sum(abs(target_t - held_{t-1}))` across assets after deterministic asset alignment.
4. Rebalance the whole eligible portfolio to the current target only when displacement is **>= 0.05**; below 0.05 retain prior eligible weights.
5. No calendar/date switches, asset identities, hand-picking, or future information are permitted. The 0.05 trigger is frozen now and will not be tuned after observing economics.

## Required integrity tests

Long-only and gross <= 1; mandatory liquidity exits; asset-order invariance; prefix/bounded-replay invariance; deterministic rerun; single-pass/multipass parity where the repository evaluator supports both; identical causal target construction between candidate and controls.

## Frozen comparisons and destructive control

Primary baseline: existing static 50/50 ensemble. Secondary reference: rejected 2% no-trade band. Destructive control: apply one additional trading-day lag to the sparse-trigger target before execution while retaining the same trigger logic.

## Frozen measurement

Use the repository's completed-history origin protocol and current IS beginning 2016-01-01. Report exact 4% / 8% / 12% ATR(14) transaction-cost sensitivity, Sharpe, annualized return, volatility, maximum drawdown, turnover, 10%-volatility-normalized return, positive-origin fraction, mean and 730-day recency-weighted origin Sharpe, and correlations to VCB and breadth-dispersion.

## Advancement gates

All must pass at the official 4%-ATR cost unless stated otherwise:

- current-IS Sharpe > 1.0 hard competition gate;
- turnover reduction versus static 50/50 >= **10%**;
- stitched completed-origin Sharpe >= **1.65748**;
- 10%-vol-normalized stitched return >= **16.57%**;
- stitched maximum drawdown >= **-12.27%**;
- 12%-ATR current-IS Sharpe > **1.0**;
- no integrity/leakage failure;
- extra-day-lag destructive control must not materially outperform the candidate.

Failure is preserved as evidence. No post-result trigger grid or threshold rescue is allowed; a later threshold study would require a separate preregistration and genuinely forward evidence.