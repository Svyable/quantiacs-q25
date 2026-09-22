# OMNI RiskCast Experts — 2026-09-19

This experiment follows the merged OMNI stock-risk attribution work but changes the target from crypto return prediction to **future crypto downside-risk forecasting**.

## Why this exists

Earlier OMNI evidence suggested that stock state can improve crypto gross-risk timing, while the original return-IC gate did not earn its complexity. Later diagnostics showed that stock tail stress and short/long realized-volatility structure were more stable risk indicators than commonality. Separately, the promoted frozen Sharpe7 carrier validated at Sharpe ~1.50 in 2023-2024 at 4% ATR cost but weakened in the post-2024 diagnostic window.

This experiment therefore freezes the crypto carrier and asks whether stock state can improve **when to carry its risk**, not which coins to own.

## Frozen mechanism

Four experts are computed from Quantiacs historical constituent panels:

- S&P 500 tail dependence;
- Nasdaq-100 tail dependence;
- S&P 500 21/126 realized-volatility term stress;
- Nasdaq-100 21/126 realized-volatility term stress.

The forecast target at origin t is the RMS of negative crypto-market returns over t+1..t+5 relative to the downside RMS already known over the prior 63 days.

An origin forecast is never scored until all five future returns have been observed. Expert losses are shifted forward five days before entering a trailing 252-observation loss window. Exponential model averaging converts those revealed losses into current expert weights.

The candidate has a second abstention layer. Its rolling ensemble MSE is compared with a persistence forecast that assumes future downside RMS equals the current 63-day downside RMS. If the ensemble does not beat persistence, health is zero and the overlay returns gross multiplier exactly to 1.

## Preregistered controls

- `base`: frozen Sharpe7 with no stock overlay.
- `static_median`: equal/median stock risk without dynamic weights or health.
- `dynamic_ungated`: dynamic loss weights but no health gate.
- `inverted`: same dynamic state and health, wrong risk direction.
- `dynamic`: candidate.

The primary decision surface is 2016-2022 at 4%, 8%, and 12% of ATR transaction-cost stress. 2023-2024 is already spent and 2025+ has been inspected elsewhere; both are diagnostic-only here and may not be used for parameter rescue.

## Integrity

The preregistration, candidate blob, and test blob are frozen before the first market measurement. Tests enforce:

- exact numerical parity of the self-contained Sharpe7 carrier with the promoted frozen carrier;
- long-only output;
- 25% name cap;
- gross <= 1;
- prefix causality;
- exact zero-health abstention;
- mechanically distinct controls.

No post-result threshold grid, floor search, horizon search, or expert-set rescue is allowed inside this experiment.

## Submission caveat

Stocks only size aggregate crypto gross and never select coin identities. The script uses Quantiacs-provided data, but Q25 cross-dataset admissibility remains a hosted/preclear item before treating this as a submission candidate.
