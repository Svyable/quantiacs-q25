# Research Method — Quantiacs Q25

**Operating system for causal, unique, low-cost crypto-long research.**

Q25 is **research-and-validation**, not “write strategy → maximize Sharpe → tweak until green.”

## Objective

Find **causal, unique, low-cost** mechanisms with a credible chance of **positive Sharpe** over the **unseen live period (2026-10-01 → 2027-01-31)**.

Prefer **residual / unique alpha** over high-Sharpe clones of public or internal cores.

Never ask *“How can I increase this backtest?”* before *“What independent causal object have we not tested, what portfolio gap could it fill, and what would falsify it?”*

## Research memory comes before ideation

Before creating a new strategy, read:

1. `configs/historical_top10.yaml` — frozen incumbent roster;
2. `configs/research_frontier.yaml` — crowded families and preferred frontier;
3. `docs/STRATEGY_ATLAS.md` — what incumbents actually measure;
4. `docs/STRATEGY_GENERATION_PLAYBOOK.md` — campaign design for new strategies.

A research agent that skips these files is likely to spend compute rediscovering an old family.

## Novelty is a pre-backtest gate

Compare a proposal with the nearest incumbent on four axes:

1. information primitive;
2. transform;
3. timing / state condition;
4. portfolio construction.

A candidate should differ on **at least two axes** before it is treated as a new independent-alpha hypothesis. One-axis changes are useful only when labeled honestly as ablations, allocator tests, controls, or family refinements.

A new lookback, threshold, top-K, rebalance day or blend weight is not a new mechanism.

## Broad-before-deep campaign design

Default discovery cadence:

- generate **24** hypotheses without performance feedback;
- score novelty, causality, falsifiability, parameter economy, cost plausibility and portfolio complement;
- preregister the best **6**;
- implement the best **3**;
- run the full pyramid;
- promote zero or more based on evidence.

The counts are defaults, not magic. The principle is more important: **diversify hypotheses before spending research looks**.

Initial candidates should usually have no more than **three free parameters**. Prefer coarse stability tests over dense lookback optimization.

## Three layers

| Layer | Role | Status rule |
|-------|------|-------------|
| **1. Rules / docs snapshot** | Contest hard rules + promotion policy (`configs/rules_snapshot.yaml`, `promotion_gates.yaml`) | Always current; dated |
| **2. Local toolbox research** | Single-pass screen → exact stats → prefix causality → multipass | Metrics only after real `qnt` runs |
| **3. Hosted Quantiacs boundary** | `strategy.ipynb` clean/check/write **or** multipass on Quantiacs host | Mark **PENDING** if not run |

Do not invent Sharpe, returns, or drawdown. Unrun evaluations = `PENDING` / empty registry fields.

## Dual research tracks

### A) `discovery` — high-capacity mechanism probe

Use enough capacity to determine whether a new information primitive appears to contain structure. This track carries a heavier multiple-testing burden and should not become an excuse for unbounded feature search.

### B) `robustness` — deliberately simple mechanism test

Few bounded signals, slower/event-driven rebalance, **cash allowed** (gross < 1 OK), **capped allocation**, no hand-picked assets, execution delay left to evaluator. See `factory/tracks.py` and `strategies/robust_weekly_waterfill.py`.

**Convergence rule:** when both tracks independently support the **same mechanism**, treat that as stronger evidence than either track alone. If only the complicated version works, assume fragility until disproven.

## Current frontier preference

The machine-readable source is `configs/research_frontier.yaml`. Current priority areas include:

- assimilation-delay dynamics;
- residual correlation-topology change;
- liquidity-transition hysteresis;
- volatility term structure / vol-of-vol;
- tail-dependence state;
- range-volume geometry;
- shock-recovery surfaces;
- nonlinear cross-sectional response;
- opportunity density / alpha breadth;
- execution-aware alpha density.

These are **research priorities, not claims of edge**.

## Iteration loop

1. **Map incumbents** — identify nearest existing family and novelty gap.
2. **Generate broadly** — idea slate before returns.
3. **Preregister** — write `preregistration.json` + SHA256 before holdout-sensitive testing (`scripts/new_experiment.py`, `research/preregister.py`).
4. **Hypothesis** — name mechanism, nearest incumbent, novelty axes, falsifier and ablation.
5. **L0–L1** — static admissibility + deterministic strategy tests (`research/static_audit.py`).
6. **Single-pass screen** — cheap exploratory stats only; do not promote on screen alone.
7. **L3 exact stats** — Quantiacs stats fields; cost ladder L4.
8. **L2 prefix** — causality / look-ahead check (`research/prefix_test.py`).
9. **L5–L6** — regimes + chronological folds; live window untouched.
10. **L7–L9** — residual vs core, multiple-testing ledger, adversarial falsification.
11. **Portfolio admission** — test marginal contribution, not just standalone metrics.
12. **Promote or kill** — gates in `configs/promotion_gates.yaml`; append to formula ledger.
13. **Hosted boundary** — only after local gates; submission checklist; mark PENDING if skipped.

## Falsification before optimization

Every serious candidate needs a destructive test that should break it if the mechanism interpretation is true.

Examples:

- sign inversion;
- lag/leader shuffle;
- state-mask inversion;
- matched-frequency random event dates;
- remove residualization;
- replace special allocator with equal weight;
- extra execution delay;
- replace the proposed primitive with a matched volatility/control primitive.

If the falsifier preserves the edge, the explanation is wrong or incomplete. Freeze the candidate instead of inventing a rescue story.

## Originality hierarchy

Originality is tested three times:

1. **Before returns** — four-axis novelty map.
2. **During research** — matched correlations / residualization against incumbent families and simple controls.
3. **At the platform boundary** — current external strategy-correlation check.

A strong raw backtest with no residual value is a family refinement, not a new alpha.

Do not tune blend weights to make a failed correlation gate barely pass.

## Compact robustness design patterns

- Quantiacs data only (`cryptodaily` + historical `is_liquid`)
- slow/event-driven rebalance where the mechanism permits
- permit cash
- capped water-fill / explicit name caps
- long-only × `is_liquid`
- optional risk modules only when they test a named hypothesis
- explicit signal-per-cost logic for execution-aware ideas

## Behavioral rules

1. No fabricated metrics. Empty / `null` / `PENDING` until a real run.
2. `API_KEY` required (blank exits). Never commit it.
3. Long-only, historical `is_liquid`, sponsor data only, no manual coin picking.
4. Hard IS Sharpe **> 1.0** since 2016-01-01.
5. Desk / firm names are inspiration only — no affiliation claimed.
6. Prefer unique residual alpha over clone Sharpe.
7. Failures are first-class: append to `experiments/` ledgers; do not delete.
8. Ask what would falsify the mechanism before tuning parameters.
9. Do not use previously observed diagnostic windows as fresh validation.
10. “No promotion” is a valid successful research outcome.

## Related docs

- [STRATEGY_GENERATION_PLAYBOOK.md](STRATEGY_GENERATION_PLAYBOOK.md) — **start here for new strategy campaigns**
- [AGENT_PROMPT.md](AGENT_PROMPT.md) — paste-ready next-agent contract
- [STRATEGY_ATLAS.md](STRATEGY_ATLAS.md) — incumbent mechanism map
- [TESTING_PYRAMID.md](TESTING_PYRAMID.md) — Levels 0–9
- [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md) — hosted `strategy.ipynb` workflow
- [`../configs/research_frontier.yaml`](../configs/research_frontier.yaml) — machine-readable novelty frontier
