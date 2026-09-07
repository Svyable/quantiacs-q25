# Testing Pyramid — Levels 0–9

Concrete checks for Quantiacs Q25 research. **No fabricated metrics.** Mark checks `PASS` / `FAIL` / `PENDING`.

## L0 — Static admissibility

Code / weight shape before any economic claim.

- [ ] Competition type is `crypto_daily_long`
- [ ] Weights long-only (no negative positions)
- [ ] Gross exposure ≤ 1 (cash permitted; unused = cash)
- [ ] Positions only where `is_liquid` (or equivalent mask)
- [ ] Finite weights (no NaN / Inf after clean)
- [ ] No external data / no hand-picked coin list
- [ ] `API_KEY` present for any toolbox I/O

Tool: `research/static_audit.py`

## L1 — Deterministic strategy tests

- [ ] Pure functions on synthetic xarray produce expected signs / sparsity
- [ ] Rebalance schedule matches design (e.g. weekly)
- [ ] Cap / water-fill invariants hold on toy panels
- [ ] Seeded RNG paths are reproducible when randomness is used

## L2 — Prefix causality

- [ ] Weights at time `t` identical when computed on data truncated at `t` vs full series prefix to `t`
- [ ] No peek at `t+1` close/volume in signal
- [ ] Multipass last-day slice consistent with single-pass path

Tool: `research/prefix_test.py` (TODO stubs if `qnt` absent)

## L3 — Exact Quantiacs stats

Record fields from a **real** `qnt` / hosted stats object only:

| Field | Notes |
|-------|--------|
| `sharpe_ratio` / IS Sharpe | Hard gate: **> 1.0** since 2016-01-01 |
| `mean_return` | |
| `volatility` | |
| `max_drawdown` | |
| `equity` (growth factor) | Not percent unless converted carefully |
| `avg_turnover` / related | |
| `avg_holding` | if available |
| `freq` / rebalance cadence | document |
| correlation vs templates | uniqueness filter |

Unrun = leave blank / `PENDING`. Never invent.

## L4 — Cost ladder

Stress transaction costs at (`configs/cost_ladder.yaml`):

`0.00`, `0.04`, `0.08`, `0.12`

- [ ] Sharpe / equity degrade gracefully (not cliff to zero only at one step)
- [ ] Strategy still economically plausible at mid ladder
- [ ] Document which cost assumption matches contest evaluator (if known)

## L5 — Temporal robustness

Regimes in `configs/regime_windows.yaml`:

Full, 2016–2018, 2019–2021, 2022–2024, 2025, 2026YTD, 3Y, 1Y, 180D, 90D, Q25-preview

- [ ] Rolling Sharpes computed per window (real runs only)
- [ ] No single-regime concentration as sole justification
- [ ] Note crypto regime breaks explicitly

## L6 — Chronological selection / walk-forward

Folds in `configs/chronological_folds.yaml`:

| Fold | Window | Use |
|------|--------|-----|
| research | 2016–2020 | hypothesis / feature search |
| dev | 2021–2022 | parameter development |
| validation | 2023–2024 | promotion decisions |
| diagnostic | 2025+ | diagnostics only |
| live | 2026-10 → 2027-01 | **untouched** until contest |

- [ ] Selection decisions use earlier folds only
- [ ] Live contest window never used for fitting

## L7 — Originality / residual alpha vs core

- [ ] Correlate vs simple cores (SMA trend, equal liquid, buy-and-hold liquid)
- [ ] Residual Sharpe / incremental R² after controlling for cores
- [ ] Reject near-clones even if raw Sharpe looks strong

## L8 — Multiple-testing / preregistration

- [ ] Experiment id + `preregistration.json` + SHA256 before holdout peek
- [ ] Formula ledger row appended (`templates/formula_ledger.csv`)
- [ ] Count of looks / variants recorded
- [ ] Soft promotion gates not retrofitted after seeing validation

## L9 — Adversarial falsification

- [ ] State falsifier up front (what result kills the thesis?)
- [ ] Sign-flip / shuffle / lag-break / liquidity-drop stress
- [ ] Cleaner mutation ≈ 0 (noise-only variant should not “pass”)
- [ ] Kill criteria executed; failures logged in `experiments/`

## Promotion

Only after L0–L9 policy in `configs/promotion_gates.yaml`. Contest-hard vs policy-soft are labeled there. Numeric soft thresholds: **TODO — human must set**.
