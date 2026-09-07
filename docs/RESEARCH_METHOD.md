# Research Method — Quantiacs Q25

**Operating system for causal, unique, low-cost crypto-long research.**

Q25 is **research-and-validation**, not “write strategy → maximize Sharpe → tweak until green.”

## Objective

Find **causal, unique, low-cost** mechanisms with a credible chance of **positive Sharpe** over the **4-month unseen live period (2026-10-01 → 2027-01-31)**.

Prefer **residual / unique alpha** over high-Sharpe clones of public cores.

Never ask *“How can I increase this backtest?”* before *“What independent mechanism have we not tested, and what would falsify it?”*

## Three layers

| Layer | Role | Status rule |
|-------|------|-------------|
| **1. Rules / docs snapshot** | Contest hard rules + promotion policy (`configs/rules_snapshot.yaml`, `promotion_gates.yaml`) | Always current; dated |
| **2. Local toolbox research** | Single-pass screen → exact stats → prefix causality → multipass | Metrics only after real `qnt` runs |
| **3. Hosted Quantiacs boundary** | `strategy.ipynb` clean/check/write **or** multipass on Quantiacs host | Mark **PENDING** if not run |

Do not invent Sharpe, returns, or drawdown. Unrun evaluations = `PENDING` / empty registry fields.

## Dual research tracks (both required)

### A) `discovery/` — high-capacity alpha factory

Rich feature ensembles: breakout, flow, tail, risk-guards. Higher capacity, heavier multiple-testing burden. See `factory/tracks.py` → `DISCOVERY`.

### B) `robustness/` — deliberately simple track

Few bounded signals, **weekly rebalance**, **cash allowed** (gross &lt; 1 OK), **capped water-fill**, no hand-picked assets, execution delay left to evaluator. See `factory/tracks.py` → `ROBUSTNESS` and `strategies/robust_weekly_waterfill.py`.

**Convergence rule:** when both tracks independently land on the **same mechanism**, treat that as stronger evidence than either track alone.

## Compact robustness design patterns

- Quantiacs data only (`cryptodaily` + `is_liquid`)
- Weekly rebalance (reduce ATR-linked turnover cost)
- Permit cash (gross exposure &lt; 1 is OK)
- Capped water-fill allocation (unused capacity stays cash)
- Long-only × `is_liquid`
- Optional modules: market-risk guards, vol targeting, drawdown fades, turnover smoothing

## Iteration loop (condensed §25)

1. **Preregister** — write `preregistration.json` + SHA256 before peeking at holdout (`scripts/new_experiment.py`, `research/preregister.py`).
2. **Hypothesis** — name the independent mechanism and a falsifier.
3. **L0–L1** — static admissibility + deterministic strategy tests (`research/static_audit.py`).
4. **Single-pass screen** — cheap exploratory stats only; do not promote on screen alone.
5. **L3 exact stats** — Quantiacs stats fields; cost ladder L4.
6. **L2 prefix** — causality / look-ahead check (`research/prefix_test.py`).
7. **L5–L6** — regimes + chronological folds; live window untouched.
8. **L7–L9** — residual vs core, multiple-testing ledger, adversarial falsification.
9. **Promote or kill** — gates in `configs/promotion_gates.yaml`; append to formula ledger.
10. **Hosted boundary** — only after local gates; submission checklist; mark PENDING if skipped.

## Behavioral rules

1. No fabricated metrics. Empty / `null` / `PENDING` until a real run.
2. `API_KEY` required (blank exits). Free profile key from Quantiacs personal page.
3. Long-only, `is_liquid`, sponsor data only, no manual coin picking.
4. Hard IS Sharpe **> 1.0** since 2016-01-01 (not 0.7).
5. Desk / firm names are **inspiration only** — no affiliation claimed.
6. Prefer unique residual alpha over clone Sharpe.
7. Failures are first-class: append to `experiments/` ledgers; do not delete.
8. Ask what would falsify the mechanism before tuning parameters.

## Related docs

- [TESTING_PYRAMID.md](TESTING_PYRAMID.md) — Levels 0–9
- [AGENT_PROMPT.md](AGENT_PROMPT.md) — paste-ready master prompt
- [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md) — hosted `strategy.ipynb` workflow
