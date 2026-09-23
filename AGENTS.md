# AGENTS.md — Q25 Research Agent Entry Point

This is the first read for any coding/research agent in this repository.

## Normative mandate

**Research Mandate V2 is authoritative for new research.**

Read first:

1. `configs/rules_snapshot.yaml` — contest hard constraints.
2. `configs/research_mandate_v2.yaml` — machine-readable research mandate.
3. `docs/RESEARCH_MANDATE_V2.md` — rationale and operating doctrine.
4. `docs/LOCAL_RESEARCH_ACCESS.md` — public/default Quantiacs execution.
5. `docs/EVIDENCE_MODEL.md` — evidence vocabulary.
6. `docs/STRATEGY_ATLAS.md` and `configs/research_frontier.yaml` — incumbents, failures, crowded families.
7. `docs/RESEARCH_METHOD.md` — execution loop.
8. `configs/promotion_gates.yaml` and `configs/cost_ladder.yaml` — admission and cost policy.

Historical preregistrations and one-shot holdout artifacts remain immutable records. They **do not impose a permanent historical holdout on new work**.

## Mission

Build the strongest reproducible Q25 **portfolio**, not the prettiest individual backtest.

Use **all completed Sponsor history**, including recent years, for research. The most recent data is often the most relevant evidence about the current market. Once a period has been observed, label later use `ADAPTIVE_REUSE`; do not pretend it is pristine out-of-sample evidence.

Only future observations that have not yet occurred are genuinely unseen.

## Default research loop

```
inspect current main + open work + evidence memory
→ repair broken measurement first
→ generate a broad candidate batch
→ evaluate causally at many rolling origins
→ retain every evaluated candidate in the search ledger
→ cluster redundant return streams
→ test recent + unweighted evidence and 4/8/12%-ATR costs
→ deep-test survivors with parameter neighborhoods + destructive controls
→ measure marginal contribution to current qualified portfolio
→ Pareto-select simple robust challengers
→ exact contest eligibility + production hardening
→ freeze only at production/live-forward boundary
→ learn from future evidence when it actually arrives
```

Do not preregister every exploratory formula. Exploration is allowed to search.

## Hard invariants — never relax

- Sponsor/Quantiacs data only for contest strategy logic.
- `competition_type = crypto_daily_long`.
- Historical `is_liquid`; automatic universe; no manual symbols.
- Long-only.
- Same causal algorithm through time; no arbitrary year/date switches.
- No lookahead, centered future information, negative shifts, or future-finalized universe membership.
- No toolbox/backtester loopholes.
- Deterministic/reproducible behavior.
- Exact official transaction cost: **4% × ATR(14) for every position-size change**.
- Use **8% and 12% × ATR** stress when judging robustness.
- Exact in-sample Sharpe since **2016-01-01 must be strictly > 1.0** for contest eligibility.
- The future contest/live interval must never be fit.
- A software/infrastructure failure is unknown economics, not a failed alpha.

## Broad experimentation mandate

Broad search is encouraged. Agents may evaluate hundreds of causal candidates across:

- cross-sectional ranks and residual signals;
- multiple horizons and decays;
- volatility, breadth, liquidity, range/volume and crash state;
- factor interactions;
- causal online models;
- execution-aware transformations;
- ensembles and simple blend rules;
- residualization against incumbent return streams.

Parameter search is allowed in exploration. So are feature interactions and blend exploration.

The cost is **accountability**: every evaluated candidate belongs in the search ledger. Do not show only the winner.

## Evidence: rolling-origin over calendar theater

New work should default to rolling-origin/prequential evaluation rather than fixed train/dev/holdout partitions.

At each historical origin, use only information available at that origin, then score what follows. Aggregate only after forward slices are generated causally.

Report both:

- ordinary/unweighted results; and
- recency-aware results using the current mandate default.

Historical periods previously used as forward tests remain valuable evidence and must retain their original labels. They are also allowed to inform later research as `ADAPTIVE_REUSE`.

## Survivor burden

Cheap search first; expensive skepticism later.

A serious survivor should earn:

- origin-level and aggregate prequential metrics;
- recent-period evidence;
- exact 4/8/12% ATR cost sensitivity;
- parameter-neighborhood/plateau stability;
- a mechanism-specific destructive control;
- simple baseline comparison;
- prefix/bounded-replay and asset-order checks where relevant;
- long-only/liquid/gross invariants;
- correlation clustering against tested candidates;
- comparison with the current qualified portfolio;
- marginal Sharpe/return contribution, drawdown overlap and turnover overlap;
- 10%-volatility-normalized economics.

A one-point optimum is weak evidence.

## Portfolio-first selection

Standalone Sharpe is not the objective function.

A lower-Sharpe strategy can be valuable if it produces independent returns, improves drawdowns, or raises the portfolio's cost-adjusted prequential performance. A high-Sharpe clone can add little.

Use Pareto frontiers. Do not force research into one mega-score.

## Freeze policy

Freeze when immutability matters:

- a production candidate is being claimed;
- a genuine future-forward observation is about to begin;
- an evidence artifact depends on proving the specification did not change.

Do not make freezing a tax on initial idea generation.

## Research memory

Preserve failures, search regions, destructive controls and infrastructure defects. Before opening a new family, inspect the strategy atlas, research frontier and recent evidence.

The lab should learn faster over time because it remembers what failed.

A successful run can promote zero strategies. It should still increase information, repair measurement, broaden high-quality search, or make the portfolio decision surface clearer.
