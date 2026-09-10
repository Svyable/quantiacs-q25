# Research Method — Quantiacs Q25

**Operating system for causal, unique, low-cost crypto-long research.**

Q25 is **research-and-validation**, not “write strategy → maximize Sharpe → tweak until green.”

## Objective

Find **causal, unique, low-cost** mechanisms with a credible chance of **positive Sharpe** over the **unseen live period (2026-10-01 → 2027-01-31)**.

Prefer **residual / unique alpha** over high-Sharpe clones of public or internal cores.

Never ask *“How can I increase this backtest?”* before *“What independent causal object have we not tested, what portfolio gap could it fill, and what would falsify it?”*

## Research memory comes before ideation

Before creating a new strategy, read:

1. `docs/LOCAL_RESEARCH_ACCESS.md` — how to run measured local research without a personal key;
2. `configs/historical_top10.yaml` — frozen incumbent roster;
3. `configs/research_frontier.yaml` — crowded families and preferred frontier;
4. `configs/external_research_leads.yaml` — public-research leads and admissibility labels;
5. `docs/STRATEGY_ATLAS.md` — what incumbents actually measure;
6. `docs/STRATEGY_GENERATION_PLAYBOOK.md` — campaign design for new strategies.

A research agent that skips these files is likely to spend compute rediscovering an old family or stop unnecessarily before measuring it.

## Local access model: measure first, authenticate only when needed

A personal Quantiacs API key is **not required for local/public-data research**. The current open-source toolbox explicitly accepts `API_KEY=default`, and its own tests use that sentinel. This repository's runner sets it before importing `qnt` when no credential is configured.

Use two distinct evidence layers:

| Access mode | Credential | Appropriate work |
|---|---|---|
| `public_default` | `API_KEY=default` | public Quantiacs data, local toolbox backtests/stats, prefix checks, cost ladders, folds, local multipass where supported |
| `authenticated` | real participant key / hosted session | participant-specific remote correlation/precheck, account identity, submission and other account-bound services |

Do not ask for a personal credential before attempting the local/public path. Do not leave local strategy metrics `PENDING` merely because a personal key is absent.

If public/default data access genuinely fails, record `BLOCKED_INFRA` with toolbox/version/access mode and preserve the exact frozen candidate. Infrastructure blocking is not alpha failure.

See [LOCAL_RESEARCH_ACCESS.md](LOCAL_RESEARCH_ACCESS.md) for source-level evidence and import-order details.

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
- run measured local/public Quantiacs research;
- run the full pyramid;
- promote zero or more based on evidence.

The counts are defaults, not magic. The principle is more important: **diversify hypotheses before spending research looks**.

Initial candidates should usually have no more than **three free parameters**. Prefer coarse stability tests over dense lookback optimization.

## Three evidence layers

| Layer | Role | Status rule |
|-------|------|-------------|
| **1. Rules / docs snapshot** | Contest hard rules + promotion policy (`configs/rules_snapshot.yaml`, `promotion_gates.yaml`) | Always current; dated |
| **2. Local toolbox research** | Public/default data → single-pass screen → exact stats → prefix causality → folds/costs/multipass | **Measure whenever executable**; `API_KEY=default` is sufficient for the public/local path |
| **3. Hosted/account-bound boundary** | Hosted notebook, participant-specific correlation/precheck, submission | Mark specific unrun account-bound checks **PENDING** |

Do not invent Sharpe, returns, or drawdown. A metric is `PENDING` only when that layer genuinely did not run or could not run.

## Dogfood the evaluator

Once a strategy is executable, use the actual Quantiacs toolbox to characterize it. Do not stop at “code compiles” or “tests pass.” Where supported, report:

- Sharpe;
- mean return and correctly derived CAGR-style return;
- Sortino / downside-risk diagnostics;
- volatility and maximum drawdown;
- turnover / holding diagnostics;
- Sharpe across the ATR cost ladder;
- chronological folds and explicitly labeled diagnostics;
- simple controls / CRYPTO10 comparison;
- prefix-causality, bounded-replay, cleaner-mutation, missed-date, long-only, gross and liquidity checks;
- matched correlations / residual alpha against incumbent streams when available.

Metrics measured with `public_default` are real **local Quantiacs-toolbox evidence**, not official participant-specific uniqueness clearance or a submission result.

## Dual research tracks

### A) `discovery` — high-capacity mechanism probe

Use enough capacity to determine whether a new information primitive appears to contain structure. This track carries a heavier multiple-testing burden and should not become an excuse for unbounded feature search.

### B) `robustness` — deliberately simple mechanism test

Few bounded signals, slower/event-driven rebalance, **cash allowed** (gross < 1 OK), **capped allocation**, no hand-picked assets, execution delay left to evaluator. See `factory/tracks.py` and `strategies/robust_weekly_waterfill.py`.

**Convergence rule:** when both tracks independently support the **same mechanism**, treat that as stronger evidence than either track alone. If only the complicated version works, assume fragility until disproven.

## Current frontier preference

The machine-readable source is `configs/research_frontier.yaml`. Current priority areas include:

- on-chain state × cross-section, conditional on current Q25 admissibility;
- forecast surprise / model disagreement;
- price-volume elasticity / absorption geometry;
- benchmark/index ecology, conditional on current Q25 admissibility;
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
6. **Initialize local access** — use the repo runner; `API_KEY=default` if no participant key exists.
7. **Single-pass screen** — cheap exploratory stats only; do not promote on screen alone.
8. **L3 exact stats** — Quantiacs stats fields; cost ladder L4.
9. **L2 prefix** — causality / look-ahead check (`research/prefix_test.py`).
10. **L5–L6** — regimes + chronological folds; live window untouched.
11. **L7–L9** — residual vs core, multiple-testing ledger, adversarial falsification.
12. **Portfolio admission** — test marginal contribution, not just standalone metrics.
13. **Promote or kill** — gates in `configs/promotion_gates.yaml`; append to formula ledger.
14. **Hosted/account boundary** — only after local gates; submission checklist; mark account-bound checks PENDING if skipped.

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
3. **At the platform boundary** — current participant-specific external strategy-correlation check.

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

1. No fabricated metrics. Empty / `null` / `PENDING` only until a real run or genuine infrastructure block.
2. **No personal API key is required for local/public research.** Initialize `API_KEY=default` before `qnt` imports when no participant key exists; real credentials are account-bound only and must never be committed or printed.
3. Long-only, historical `is_liquid`, sponsor data only, no manual coin picking.
4. Hard IS Sharpe **> 1.0** since 2016-01-01.
5. Desk / firm names are inspiration only — no affiliation claimed.
6. Prefer unique residual alpha over clone Sharpe.
7. Failures are first-class: append to `experiments/` ledgers; do not delete.
8. Ask what would falsify the mechanism before tuning parameters.
9. Do not use previously observed diagnostic windows as fresh validation.
10. “No promotion” is a valid successful research outcome.
11. **Dogfood the evaluator:** an executable strategy with reachable public data should produce measured local evidence, not credential-based excuses.

## Related docs

- [LOCAL_RESEARCH_ACCESS.md](LOCAL_RESEARCH_ACCESS.md) — credential-free local/public Quantiacs research and authenticated boundary
- [STRATEGY_GENERATION_PLAYBOOK.md](STRATEGY_GENERATION_PLAYBOOK.md) — **start here for new strategy campaigns**
- [AGENT_PROMPT.md](AGENT_PROMPT.md) — paste-ready next-agent contract
- [STRATEGY_ATLAS.md](STRATEGY_ATLAS.md) — incumbent mechanism map
- [TESTING_PYRAMID.md](TESTING_PYRAMID.md) — Levels 0–9
- [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md) — hosted/account-bound workflow
- [`../configs/research_frontier.yaml`](../configs/research_frontier.yaml) — machine-readable novelty frontier
