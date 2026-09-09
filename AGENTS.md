# AGENTS.md — Q25 Research Agent Entry Point

This file is the **first read for any coding/research agent** working in this repository.

Your mission is not to produce more strategy files. Your mission is to discover, falsify and document **causal, distinct, Q25-admissible mechanisms** that add portfolio value beyond the incumbent research stack.

## Mandatory reading order

Before proposing code or running a backtest, read:

1. `configs/rules_snapshot.yaml`
2. `docs/AGENT_PROMPT.md`
3. `configs/historical_top10.yaml`
4. `configs/research_frontier.yaml`
5. `configs/external_research_leads.yaml`
6. `docs/EXTERNAL_RESEARCH_LEADS.md`
7. `docs/STRATEGY_ATLAS.md`
8. `docs/STRATEGY_GENERATION_PLAYBOOK.md`
9. `docs/RESEARCH_METHOD.md`
10. `docs/TESTING_PYRAMID.md`
11. `configs/promotion_gates.yaml`
12. `configs/chronological_folds.yaml`
13. `configs/cost_ladder.yaml`

Also inspect `strategies/q25_sota_meta_ensemble.py` before calling any residual-momentum / volume-response / co-crash / residual-skew / path-efficiency idea new.

## Current external-intelligence update

The public Q24/Q25 sweep surfaced four especially useful research directions:

1. **On-chain state × cross-section** — official Q24 docs demonstrate Quantiacs blockchain loaders. Q25 use is **not yet assumed admissible**; verify current rules, loader behavior and timestamps first.
2. **Online forecast surprise / model disagreement** — inspired by public stateful Quantiacs code and official rolling-ML examples, but implement as tiny causal models with explicit non-ML ablations.
3. **Price-volume elasticity / absorption geometry** — OHLCV-only, but must remain distinct from V12 directed volume diffusion.
4. **CRYPTO10 benchmark-composition ecology** — potentially new market-cap state if historical benchmark weights are currently available and Q25-permitted; otherwise fall back to `is_liquid`-only lifecycle research.

A simple **persistent low-volatility selector** is also worth reproducing as an external control, not as a novelty claim.

Read `docs/EXTERNAL_RESEARCH_LEADS.md` for source URLs, caveats, candidate formulations, falsifiers and contamination notes.

## Internet evidence discipline

Never treat public material as trusted strategy evidence.

- Official docs: useful for rules/API capabilities.
- Official examples: useful for mechanics, not alpha proof.
- Third-party code: idea source only until audited/reproduced.
- Leaderboard title: breadcrumb only; never reverse-engineer a formula from the name.
- Public Sharpe/CAGR/DD: untrusted until independently reproduced under this repo's conventions.
- Current Q25 preview/OOS: diagnostic and contaminated, often based on very few post-submission days.

Record the external source URL in preregistration whenever it materially inspired the hypothesis.

## Data-admissibility rule

`Quantiacs-provided` is necessary but **do not assume it is sufficient for Q25** merely because a loader exists or was allowed in Q24.

For any nonstandard data source such as blockchain or benchmark weights, verify before implementation/promotion:

- current Q25 rules;
- current loader availability;
- decision-time publication semantics;
- revisions/backfills;
- historical replay/multipass behavior;
- runtime.

Until verified, mark the primitive `UNVERIFIED_FOR_Q25` and keep it out of a submission candidate.

## Novelty gate before returns

For every proposed independent alpha, compare it to the nearest incumbent across:

1. information primitive;
2. transform;
3. timing/state condition;
4. portfolio construction.

Require at least **two changed axes** before calling it a new alpha family.

A new lookback, threshold, smoothing constant, rebalance day, top-K, risk cap, classifier type or blend weight is not sufficient.

## Default campaign

Run broad-before-deep:

```text
24 hypothesis sketches
→ novelty/falsifiability scoring before returns
→ 6 preregistrations
→ up to 3 implementations
→ L0-L9 + falsifiers + costs + folds + residual/correlation
→ promote / reserve / kill
```

For the next campaign, the external-intelligence allocation is:

- 7 on-chain-state hypotheses;
- 7 forecast-surprise/disagreement hypotheses;
- 5 price-volume-elasticity hypotheses;
- 5 benchmark/index-ecology hypotheses.

If on-chain/index data fail Q25 admissibility, reallocate those slots to OHLCV-only surprise, topology, vol-term, liquidity-hysteresis and range-volume research. Do not force uncertain data into the contest path.

## Candidate contract

Before deeper testing, write down:

```text
ID:
Track: discovery | robustness
Source/inspiration URL(s):
Mechanism family:
One-sentence thesis:
Raw information primitive:
Q25 data admissibility: VERIFIED | UNVERIFIED
Transform into score:
Decision-time availability:
Timing/state condition:
Selection rule:
Allocation rule:
Cash rule:
Rebalance rule:
Initial free parameters: <= 3
Nearest incumbent:
Novelty axes changed:
Why this is not an incumbent variant:
Primary falsifier:
Ablation:
Expected failure mode:
Cost hypothesis:
Portfolio role if it works:
Contamination notes:
```

If the source inspired the idea but the mechanism cannot be stated independently, do not backtest it yet.

## Strong next hypotheses

These are examples to seed ideation, not instructions to blindly implement all of them.

### On-chain / network state

- network stress × age since `is_liquid` entry;
- on-chain / price disagreement;
- network state × self price-volume elasticity;
- network acceleration × residual forecast surprise;
- on-chain state-transition events;
- state persistence / duration;
- 2–3 metric agreement only after single-metric mechanisms survive.

### Forecast surprise / disagreement

- residual surprise continuation;
- residual surprise reversal — separate preregistration, not post-hoc direction choice;
- model calibration drift as regime state;
- surprise half-life;
- two-model disagreement as cash gate;
- disagreement × liquidity age;
- topology of forecast errors rather than topology of raw returns.

### Price-volume elasticity

- abnormal volume consumed per unit directional displacement;
- range displacement per abnormal dollar volume;
- close-location × flow absorption;
- failed displacement after high flow;
- elasticity acceleration/compression relative to own history.

### Index ecology — conditional on data permission

- benchmark concentration / effective number of names;
- member weight acceleration;
- market-cap rank migration;
- entrant/re-entry trajectory;
- leadership turnover;
- concentration shock × liquidity age.

## Required falsification style

Mechanism-specific destructive controls should be stronger than generic parameter sensitivity.

Examples:

- shuffle external state dates at matched frequency;
- replace on-chain state with matched market-vol state;
- replace forecast surprise with raw residual return;
- freeze online model coefficients;
- permute model identities for disagreement tests;
- destroy price-volume pairing while preserving marginal ranks;
- replace exact benchmark-weight dynamics with binary `is_liquid` only;
- add extra execution delay;
- invert the state gate.

If the destructive control preserves the edge, the mechanism story is wrong or incomplete.

## ML rule

Do not use ML as a substitute for a hypothesis.

Good:

> classify continuation vs reversal of a predeclared residual-surprise state using three causal inputs.

Bad:

> feed a large indicator zoo into XGBoost and optimize Sharpe.

Start with ridge/OLS/EWMA/simple classifiers. Always compare to the same mechanism without ML.

## Low-turnover preference

The public Q24 leaderboard reports the winner with very low average turnover. This does **not** reveal the winner's signal, but it reinforces a portfolio principle:

> when evidence is comparable, prefer the mechanism that earns information with less unnecessary position movement.

Naturally persistent/event-driven alpha is preferable to post-hoc smoothing of a churning signal.

## Public controls worth reproducing

Reimplement independently, do not copy metrics:

- persistent low-volatility selection;
- equal-liquid;
- inverse-vol trend;
- generic cross-sectional momentum;
- simple classifier/non-ML baseline for any ML experiment.

Controls are there to embarrass complicated ideas.

## Hard prohibitions

- no fabricated metrics;
- no future leakage;
- no centered windows / negative shifts / future-known membership;
- no manual symbols;
- no external non-Quantiacs strategy data in a contest strategy;
- no full-history Sharpe hyperparameter search as evidence;
- no rescuing a failed correlation gate by blend-weight tuning;
- no promotion from a single narrow parameter optimum;
- no claiming public leaderboard titles reveal implementation;
- no importing public performance claims into our registry;
- no touching the 2026-10-01 → 2027-01-31 live window for fitting/selection.

## Definition of a successful agent run

A successful run may promote **zero** strategies.

Success means the repo ends with more information:

- a broad idea slate;
- source-aware preregistrations;
- causal implementations;
- explicit failed falsifiers / kills;
- independent control comparisons;
- residual/correlation evidence;
- a clear statement of what frontier shrank or expanded.

The goal is not strategy count. The goal is **independent information per research look**.
