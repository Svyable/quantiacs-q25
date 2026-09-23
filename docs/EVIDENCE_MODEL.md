---
title: Evidence Model
description: Q25 evidence vocabulary under Research Mandate V2.
---

# Evidence model

Q25 separates **economic quality**, **evidence provenance**, and **implementation health**. Never collapse them into one status.

Research Mandate V2 uses all completed Sponsor history. Evidence strength comes from how a result was generated and how much adaptive search touched it, not from assigning moral value to calendar years.

## Evidence provenance

| Label | Meaning |
|---|---|
| `EXPLORATORY` | Result was available to idea generation, parameter search, feature selection or blend search. Useful, but carries search/adaptation burden. |
| `PREQUENTIAL` | At each historical origin, the scored outcome was future relative to the information available at that origin under the declared rolling procedure. |
| `ADAPTIVE_REUSE` | Historical observations had been inspected before and are reused in later research. Informative, especially when recent, but not pristine confirmation. |
| `LIVE_FORWARD` | Observation occurred after the production specification was frozen. Strongest genuinely future evidence. |
| `BLOCKED_INFRA` | Execution or measurement failed. Economics are unknown. |
| `HISTORICAL_FROZEN` | Immutable legacy packet retaining the evidence semantics used when it was created. |

A result can have multiple useful descriptors. For example, a batch can be `PREQUENTIAL` in construction while also being part of an `EXPLORATORY` search process.

## Historical holdouts

Old one-shot validation/holdout artifacts remain immutable. Their original hashes, decisions and claims must not be rewritten.

Those historical dates are nevertheless available to new V2 research. Later use is `ADAPTIVE_REUSE`. Reusing the dates does not retroactively change the old artifact, and refreezing before another replay does not make the dates pristine again.

## Strategy quality

Economic evaluation should expose a vector rather than one rank:

- full-history and origin-level Sharpe;
- recent prequential Sharpe;
- recency-weighted and unweighted results;
- annualized return/volatility;
- 10%-vol normalized return;
- max drawdown;
- turnover;
- official and stressed transaction-cost sensitivity;
- parameter-neighborhood stability;
- regime stability;
- correlation, drawdown overlap and turnover overlap;
- marginal contribution to the current qualified portfolio.

Standalone Sharpe is not the primary objective.

## Search provenance

Every evaluated candidate in a broad search belongs in the search ledger. Preserve:

- formula/strategy identity and parameters;
- family/parent;
- source revision;
- evaluation origins;
- cost assumptions;
- metrics;
- status/failure stage;
- search batch identity;
- return-stream hash when practical.

The winner of a 500-cell batch is not equivalent evidence to a single prespecified test. Keep the search footprint visible.

## Implementation health

Implementation checks remain orthogonal to economics:

- admissible Sponsor data;
- historical liquidity;
- long-only and gross constraints;
- no lookahead;
- deterministic behavior;
- asset-order invariance where relevant;
- prefix/bounded replay;
- cleaner/runtime checks;
- single/multipass parity where applicable;
- production adapter identity.

A red implementation cell means unknown economics until repaired. It is not a zero Sharpe.

## Survivor evidence

Cheap exploratory search should be broad. Expensive skepticism should be concentrated on survivors.

Before a serious promotion claim, a survivor should normally have:

1. repeated causal rolling-origin evidence;
2. recent as well as long-history evidence;
3. 4/8/12%-ATR cost results;
4. a parameter-neighborhood/plateau check;
5. a simple baseline;
6. a mechanism-specific destructive control;
7. correlation clustering and incumbent comparisons;
8. portfolio marginal-contribution analysis;
9. contest hard-gate verification.

## Portfolio decision

Use Pareto frontiers, not a universal mega-score.

A lower standalone Sharpe candidate may be superior portfolio material if it diversifies incumbent returns or drawdowns. A high-Sharpe clone may contribute almost nothing.

Production selection should prefer simple, reproducible mechanisms whose advantage is stable across nearby choices rather than a fragile peak.

## Future truth

Only observations that have not happened yet are truly unseen.

Before the Q25 live period occurs, it may not be used. Once future observations arrive, preserve their original `LIVE_FORWARD` timestamp/evidence record; they may later join the completed research history as `ADAPTIVE_REUSE`.

[Research Mandate V2](RESEARCH_MANDATE_V2.md) · [Research method](RESEARCH_METHOD.md)
