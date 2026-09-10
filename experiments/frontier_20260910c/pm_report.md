# Frontier-C new-alpha campaign — 2026-09-10

Decision before measurement: **registered development research; zero Frontier-C returns observed.**

This campaign is intentionally not a rescue of Frontier-A. The first exact Frontier-A measurement killed simple AR forecast surprise, simple price/volume absorption, and standalone volatility-curve shape. Frontier-B separately killed standalone liquidity hysteresis and shock-recovery surface while leaving topology migration as the strongest new development family.

Frontier-C therefore changes the information object rather than retuning those formulas.

## Implemented hypotheses

1. **signed risk transition** — falling downside residual semivariance relative to upside semivariance, conditioned on positive residual trend.
2. **positive tail decay** — positive residual trend whose rolling variance is becoming less concentrated in one extreme positive observation.
3. **assimilation acceleration** — positive residual trend while the asset's common-market response centroid moves toward shorter lags.

Each has three coarse preregistered lookbacks (42/63/84), a canonical 63-day parent, an ablation, and a label-rotation falsifier. Allocation is weekly, top five, max 25% per name, with cash allowed and immediate strict-liquidity exits.

## Registered reserves

- downside beta decoupling
- response sign asymmetry
- topology reconnection

These are preregistered but **not implemented**. A disappointing measured result from an implemented family does not authorize automatically switching to a reserve or tuning a failed formula.

## Evidence boundary

Frontier-A and Frontier-B development results were observed before this campaign was designed, so 2016-2022 is explicitly reused development evidence, not a fresh holdout. The score table in `idea_slate.json` was frozen before any Frontier-C return was observed. Selection remains restricted to research (2016-2020) and dev (2021-2022), with the same 0/4/8/12% ATR-linked cost ladder and fixed development floor.

2023-2024 validation and later diagnostic/live periods are not allowed to drive mutation. No official contest qualification, hosted uniqueness, or submission claim is made here.

## Kill rules

A family freezes if its canonical ablation/falsifier matches or beats its parent, or if every valid base cell remains below the fixed development Sharpe floor. A single attractive lookback is not a new hypothesis and will not trigger local tuning. If all three fail, the next campaign must move to a materially different primitive/state interaction.

## Source use

Published downside-risk, signed-volatility/jump, and crypto lead-lag work motivates the questions only. No external strategy weights, tuned thresholds, reported Sharpe values, or manually selected symbols enter the implementations.
