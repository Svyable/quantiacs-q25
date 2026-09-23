# Research Mandate V2 — Prequential Alpha Factory

This document is normative for new Q25 research. Historical experiment freezes remain valid records of what was done, but they no longer define the research architecture.

## Core doctrine

Use **all completed Quantiacs/Sponsor history**, including the most recent years, because the current crypto regime is part of the problem we are trying to solve. A calendar period does not become useless merely because it has been inspected. It becomes **observed evidence** and must be labeled honestly.

The only truly unseen observations are those that have not happened yet.

We therefore replace the old permanent train/dev/holdout doctrine with a **prequential alpha factory**:

```
broad search
→ rolling-origin / walk-forward simulation
→ recency-aware evidence
→ destructive controls and parameter plateaus
→ correlation clustering
→ marginal portfolio contribution
→ exact contest eligibility
→ simple production freeze
→ genuine future live evidence
```

## What remains rigid

Research freedom does not weaken contest or causal integrity. Every production-capable strategy must still use Sponsor-provided Q25 data only, historical `is_liquid`, automatic asset selection, long-only weights, one quantitative algorithm through time, no manual symbols, no lookahead, no toolbox loopholes, deterministic behavior, and the official 4%×ATR(14) transaction-cost model. Stress 8% and 12%×ATR when comparing robustness.

The contest in-sample Sharpe from 2016-01-01 must remain strictly above 1.0.

The future contest/live interval is never fit because it does not yet exist at research time.

## No permanent historical embargo

Do **not** reserve 2023+, 2024+, or the latest two years as permanent untouchable holdouts for new research.

Those years contain high-value evidence about the present market. They may be used in hypothesis generation, parameter estimation, factor selection, ensemble construction, and robustness analysis, subject to honest adaptive-reuse labeling.

Do not call an already observed interval “out of sample” merely because a candidate was frozen before replaying it again.

Historical one-shot holdout experiments already in the repository remain immutable evidence packets. They are not deleted or rewritten. They simply stop acting as a veto on future learning from the same historical observations.

## Rolling-origin evidence

The primary validation object is a sequence of historical decisions.

For origins `t_1 ... t_n`:

```
information available through t_i
→ fit/select/calibrate using the declared algorithm
→ generate weights after t_i
→ score the next horizon
```

Aggregate the forward slices only after each slice has been generated causally.

Use at least eight origins when history permits; quarterly origins with roughly 90-day forward horizons are the default starting point, not an immutable law. Where labels or targets overlap, purge enough observations to prevent leakage.

Report origin-level results. A good aggregate hiding repeated origin failures is weak evidence.

## Recency is information

Default research reports include both unweighted and recency-weighted evidence. The initial default is exponential weighting with a 730-day half-life.

Recency weighting is not a calendar regime switch. The same weighting rule applies at every date and only uses observations already available at that date.

Recent evidence may therefore influence selection more than 2016 evidence while the underlying algorithm remains time-consistent.

## Broad experimentation is explicitly allowed

Exploration may use parameter search, operator search, factor interactions, residualization, multiple horizons, regime interactions, execution rules, ensemble construction, and automated batches.

A batch may evaluate hundreds of candidates.

This freedom creates a multiple-testing burden, so every evaluated candidate must be written to the search ledger. Failed candidates and failed search regions are assets: preserve them so later agents do not rediscover them.

Preregistration is **not required for every exploratory idea**. Freeze a specification when making a specific production claim, running a genuine future-forward test, or creating evidence that depends on the specification not changing afterward.

## Optimize the portfolio, not the beauty contest

Standalone Sharpe is diagnostic, not the sole objective.

A candidate should be judged by its contribution to the best currently qualified portfolio. Important dimensions include:

- marginal portfolio Sharpe or utility;
- correlation to incumbent return streams;
- drawdown overlap;
- turnover overlap and execution cost;
- recent prequential performance;
- full-history performance;
- cost sensitivity;
- parameter-neighborhood stability;
- regime dependence;
- implementation simplicity;
- 10%-volatility-normalized return.

A modest standalone factor can be valuable when it diversifies VCB or another incumbent. A spectacular clone can be nearly worthless.

Use Pareto frontiers and clustering instead of forcing every research result through one scalar score.

## Parameter search without parameter worship

Search is allowed. One-point optima are not persuasive.

For survivors, measure a coarse neighborhood around the selected parameters. Prefer wide plateaus and monotonic economic relationships. Penalize fragile complexity. If small perturbations destroy the result, treat the strategy as fragile even if its best point is excellent.

A result discovered after a large search must retain its search footprint in the evidence packet.

## Destructive controls remain mandatory for serious survivors

A compelling strategy should survive tests that attack its claimed mechanism: identity permutation, lag perturbation, removal of residualization, matched generic state replacement, execution delay, allocator simplification, or another mechanism-specific falsifier.

Controls do not need to be preregistered before initial exploration. They do need to be specified and run before a survivor is promoted as a credible mechanism.

## Evidence labels

Use these terms precisely:

- **EXPLORATORY** — used to generate or tune ideas.
- **PREQUENTIAL** — forward relative to each historical rolling origin under a declared procedure.
- **ADAPTIVE_REUSE** — previously inspected history reused in later research.
- **LIVE_FORWARD** — observations that occurred only after a production freeze.
- **BLOCKED_INFRA** — no valid economic conclusion because measurement failed.

Never convert an infrastructure exception into a Sharpe of zero or a falsified hypothesis.

## Champion–challenger loop

The production portfolio is a champion, not a sacred endpoint.

New challengers are generated using all completed history and compared through the same rolling-origin and exact-cost machinery. Production changes should favor simple, reproducible combinations with material incremental value rather than tiny backtest improvements.

After deployment, new observations become genuine forward evidence. They may later become research data as well; retain their original forward timestamp and evidence label.

## Agent mandate

Every autonomous research run should maximize **information gain per unit of compute and repository complexity**.

Repair broken measurement first. Then prefer broad batches over isolated pet hypotheses. Record the search footprint. Cluster redundant candidates. Deep-test only survivors. Preserve failures. Compare survivors to the current portfolio. Freeze only at the boundary where immutability actually matters.

The repository should evolve toward a research factory capable of producing many weak, differentiated signals and combining them intelligently—not a sequence of ceremonial one-shot backtests.
