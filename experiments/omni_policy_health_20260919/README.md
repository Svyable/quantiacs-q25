# OMNI Policy Health — 2026-09-19

This is a new experiment, not a retune of the failed RiskCast MSE-health gate.

## Hypothesis

The fixed stock-risk overlay can be a useful policy even when its raw risk forecast remains statistically accurate but economically harmful. Therefore health should be measured against the **contest objective** rather than against forecast MSE.

Two policies are frozen:

1. `base`: promoted Sharpe7 Vol2.
2. `always_static`: the exact static SPX/NDX tail + vol-term risk overlay from frozen RiskCast, with the same 0.35 risk floor and 0.10 cut band.

The new selector observes only already-realized hypothetical returns. Policy return on day t is previous-day policy weights multiplied by crypto close-to-close return ending at t.

Every Monday, the candidate compares trailing annualized Sharpe for the two policies over 126 and 252 days. It enables the stock overlay for the coming week only if the overlay has the higher Sharpe on **both** horizons. Otherwise it uses base.

## Why the health calculation is cost-free

The internal gate does not attempt to approximate Quantiacs' ATR slippage. That would introduce another model and another tunable approximation. Instead, the policy gate is explicitly a cost-free utility proxy; final evidence is measured by the exact Quantiacs evaluator at 4%, 8%, and 12% of ATR.

## Controls

- `base`: no stock risk timing.
- `always_static`: fixed overlay always active.
- `fast_only`: 126-day policy health only.
- `slow_only`: 252-day policy health only.
- `inverted_dual`: overlay is enabled only when it has underperformed base on both horizons.
- `dual`: preregistered candidate.

No margin threshold, grid, hysteresis parameter, or post-result window search is allowed.

## Selection discipline

The only selection surface is 2016-2022. Results from 2023-2024 and 2025+ are already contaminated/spent and are reported only as diagnostics. They may not trigger a parameter rescue.

## Submission caveat

Stocks never select a crypto asset and all inputs are Quantiacs-provided, but cross-dataset Q25 admissibility still requires hosted/preclear before this can be treated as a submission artifact.
