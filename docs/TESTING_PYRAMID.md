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
- [ ] Quantiacs access initialized **before** any `qnt` import; `API_KEY=default` is sufficient for local/public research and no personal credential is required

Tool: `research/static_audit.py`

See `docs/LOCAL_RESEARCH_ACCESS.md` for the public/default vs authenticated boundary.

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

Record fields from a **real** `qnt` / hosted stats object only. Local runs using `API_KEY=default` count as **observed local Quantiacs-toolbox evidence**; they do not count as participant-specific uniqueness clearance or submission evidence.

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
| correlation vs templates | local diagnostic unless participant-specific remote check actually ran |

- [ ] Access provenance recorded as `public_default` or `authenticated`, never the credential itself
- [ ] Executable candidates were actually measured when public/default data were reachable
- [ ] Local metrics and account-bound/hosted metrics are labeled separately

Unrun = leave blank / `PENDING`. A missing **personal** key is not a valid reason for local-toolbox PENDING; attempt the public/default path first. Never invent.

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
- [ ] Previously inspected 2025/Q25-preview windows labeled diagnostic, not fresh holdout

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
- [ ] Participant-specific remote uniqueness/correlation remains a separate hosted/account-bound check

## L8 — Multiple-testing / preregistration

- [ ] Experiment id + `preregistration.json` + SHA256 before holdout peek
- [ ] Formula ledger row appended (`templates/formula_ledger.csv`)
- [ ] Count of looks / variants recorded
- [ ] Soft promotion gates not retrofitted after seeing validation

## L9 — Adversarial falsification

- [ ] State falsifier up front (what result kills the thesis?)
- [ ] Check allocator identifiability: count changed target days versus the ablation. A score interaction discarded by the allocator is not additional deployed alpha.
- [ ] Cross-sectional permutations preserve the eligible, finite marginal distribution and remain invariant to asset order or inactive future-listed columns.
- [ ] Sign-flip / shuffle / lag-break / liquidity-drop stress
- [ ] Cleaner mutation ≈ 0 (noise-only variant should not “pass”)
- [ ] Kill criteria executed; failures logged in `experiments/`

`research/mechanism_diagnostics.py` provides target-path comparisons and paired
circular block-bootstrap intervals. Freeze the block length, seed, number of
draws and comparison before inspecting returns. Intervals on reused development
data are diagnostics, not selection-adjusted significance or promotion gates.
See `scripts/analyze_mechanism_controls.py` for source/data-hash-checked use.

## Infrastructure vs alpha failure

If the public/default toolbox or data endpoint genuinely fails, record `BLOCKED_INFRA` with the safe access mode and frozen code identity. Do not count that as an alpha failure and do not change strategy parameters while repairing infrastructure.

## Promotion

Only after L0–L9 policy in `configs/promotion_gates.yaml`. Contest-hard vs policy-soft are labeled there. Numeric soft thresholds: **TODO — human must set**.
