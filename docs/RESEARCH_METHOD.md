# Research Method — Quantiacs Q25

The normative policy for new work is [Research Mandate V2](RESEARCH_MANDATE_V2.md) and `configs/research_mandate_v2.yaml`.

## Objective

Discover and combine causal Q25 signals that improve the **current portfolio** after exact transaction costs, while satisfying contest hard constraints.

The research system uses all completed Sponsor history. It does not maintain a permanent historical holdout. Statistical honesty comes from causal rolling-origin evaluation, explicit adaptive-reuse labels, search accounting, robustness tests, and genuine future evidence.

## 1. Inspect before searching

Before new experiments:

- inspect current `main`, open PRs and failing workflows;
- repair measurement/reproducibility blockers first;
- read the strategy atlas and research frontier;
- inspect recent evidence and failed families;
- identify the current qualified champion portfolio and nearest family peers.

A new filename is not a new idea.

Local measurement should not wait for participant credentials: use the repository public/default path with `API_KEY=default` before importing `qnt` when no personal key is configured. Account-bound credentials are only for participant-specific services.

## 2. Search broadly

Create batches rather than isolated pet hypotheses.

Exploration may search parameters, horizons, operators, interactions, residualizations and simple blends. Prefer economically interpretable primitives, but do not artificially limit the search to three parameters or a tiny number of formulas.

Record the entire candidate set and search footprint.

Exploratory performance is allowed to influence the next experiment. Label it honestly as exploration/adaptive reuse rather than pretending it is independent confirmation.

## 3. Evaluate prequentially

Default to repeated rolling origins.

At each origin `t`:

1. expose only information available through `t`;
2. run the same declared fitting/selection algorithm;
3. generate post-`t` weights;
4. score the forward horizon;
5. retain origin-level metrics.

Use expanding or rolling estimation according to the mechanism. Purge overlapping targets when necessary.

The default starting configuration is quarterly origins, ~90-day forward horizons, at least eight origins where history permits. These values may be changed for mechanism fit, but the procedure must remain causal and be reported.

## 4. Make recent data count

Report ordinary and recency-weighted evidence. The V2 default half-life is 730 days.

A fixed exponential decay is allowed because it is the same rule through time. A hand-written switch such as “after 2024 use different weights” is not.

Recent history may influence training, selection and ensemble composition.

## 5. Account for search

Every tested candidate belongs in the experiment/search ledger, including failures.

For each batch retain at least:

- formula/strategy identity;
- parameters;
- parent/family;
- source revision;
- evaluation origins;
- costs;
- aggregate and recent metrics;
- status/failure stage;
- return-stream hash when practical.

For heavily searched families, prefer block-bootstrap or equivalent search-bias diagnostics before treating the top cell as strong evidence.

## 6. Funnel by cost

Do not run expensive tests on everything.

Cheap stage:
- admissibility/static checks;
- causal formula construction;
- approximate or exact 4% screen;
- rolling-origin return generation;
- correlation clustering.

Survivor stage:
- exact 4/8/12%-ATR economics;
- parameter neighborhoods;
- destructive controls;
- prefix/bounded replay;
- deterministic and asset-order invariance tests;
- runtime/cleaner checks;
- regime and recent-origin stability;
- portfolio marginal contribution.

Production stage:
- exact full IS eligibility;
- single/multipass parity where applicable;
- current correlation/uniqueness checks;
- production adapter identity;
- live-forward freeze.

## 7. Portfolio-first decision

Do not select solely by standalone Sharpe.

Compare each survivor with the current qualified portfolio on:

- marginal portfolio Sharpe/utility;
- correlation;
- drawdown overlap;
- turnover overlap;
- cost robustness;
- recent prequential Sharpe;
- full-history Sharpe;
- max drawdown;
- 10%-vol normalized return;
- complexity.

Cluster highly redundant candidates. Prefer a small set of complementary signals over a zoo of near-duplicates.

Blend search is allowed during exploration. Production should use a simple rule that is stable over a broad weight neighborhood.

## 8. Falsify survivors

Every serious survivor needs a mechanism-specific destructive control and a simple baseline.

Examples include identity permutation, time/lag perturbation, removing residualization, replacing a special state with a generic matched state, simplifying the allocator, or adding execution delay.

If a control preserves the edge, the interpretation is weakened even when the return stream is attractive.

## 9. Evidence vocabulary

- `EXPLORATORY`: influenced search or tuning.
- `PREQUENTIAL`: generated forward relative to each historical origin.
- `ADAPTIVE_REUSE`: already-observed history reused in later research.
- `LIVE_FORWARD`: genuinely future observations after a production freeze.
- `BLOCKED_INFRA`: no economic conclusion.

Do not call an observed historical period pristine OOS.

## 10. Historical freezes

Existing train/dev/validation/holdout artifacts are preserved exactly as historical evidence. Their original claims and hashes remain valid.

They do not prevent future agents from using those dates in new research. Later use must be labeled adaptive reuse and cannot retroactively upgrade old evidence.

## 11. Hard contest boundary

No methodology freedom overrides:

- Sponsor data only;
- automatic top-10 liquid universe;
- long-only;
- no manual assets;
- no lookahead;
- same algorithm through time;
- official cost model;
- deterministic execution;
- IS Sharpe > 1.0 since 2016-01-01;
- required platform uniqueness/correlation checks;
- future live data never used before it exists.

## 12. Repository completion rule

A research run is complete when it leaves a reproducible artifact: code/config/docs, objective tests, an evidence/search record when economics were run, a dedicated branch/PR, and a clear next experiment.

Failures are preserved, not erased.
