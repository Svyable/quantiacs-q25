# OMNI Crash Consensus — 2026-09-19

This experiment is a new state-conjunction mechanism. It does not retune either failed health gate.

## Surviving prior evidence

Two independent experiments preserved the same useful primitive: a fixed stock-risk overlay improved frozen Sharpe7 on the 2016-2022 selection surface. Two different health systems failed:

- forecast-MSE health;
- trailing policy-Sharpe health.

The next question is therefore not "is the risk forecast healthy?" but "is this a genuine systemic crash state?"

## Candidate

Four stock experts are frozen:

- SPX tail dependence;
- NDX tail dependence;
- SPX 21/126 realized-volatility term;
- NDX 21/126 realized-volatility term.

Each expert votes stress when its robust-unit score is above 0.5. Because 0.5 is the rolling median of the robust transform, this is not a fitted numeric threshold.

Crypto independently votes fragility when:

- 21-day equal-weight crypto market log momentum is negative; and
- 21-day crypto market realized volatility exceeds 126-day volatility.

The preregistered candidate `cross_majority` activates the frozen risk sizing law only when at least three stock experts vote stress **and** crypto is fragile.

## Controls

- `base`
- `always_static`
- `stock_majority`
- `stock_unanimous`
- `crypto_only`
- `cross_unanimous`
- `inverted_cross`
- `cross_majority` candidate

## Hard evidence requirements

The candidate must improve 4%-ATR Sharpe over base separately on:

- 2016-2020 research;
- 2021-2022 development.

It must also beat the inverted control, stock-only majority, and crypto-only fragility on pooled 2016-2022 evidence, while pooled improvement must survive 8% and 12% ATR cost stress.

2023+ remains diagnostic-only and may not be used for parameter rescue.

## Contest caveat

The strategy remains long-only Crypto Top-10/liquid and stocks only alter gross sizing. Cross-dataset admissibility still requires hosted/preclear before submission.
