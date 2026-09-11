---
title: Q25 Quantitative Research Lab
description: Evidence-aware crypto alpha research for Quantiacs Q25 — causal mechanisms, measured development packets, and a ranked portfolio stack.
---

# Q25 Quantitative Research Lab

> **Build mechanisms. Measure them with the same harness. Keep failures visible.**

This is the public research dashboard for the Quantiacs Q25 Crypto Top-10 Long program. The repo is the evidence source of truth; this site is the fast way to see **what is ranked, what is merely promising, what failed, and what still needs forward evidence**.

[**Research Matrix**](RESEARCH_MATRIX.md) · [Strategy Atlas](STRATEGY_ATLAS.md) · [Evidence Model](EVIDENCE_MODEL.md) · [Research Method](RESEARCH_METHOD.md) · [Testing Pyramid](TESTING_PYRAMID.md) · [Agent Playbook](STRATEGY_GENERATION_PLAYBOOK.md)

---

## Lab pulse

| Current object | State | Why it matters |
|---|---:|---|
| **Latest measured campaign** | **Frontier-G — promote zero** | 18/18 exact cells complete; three new families frozen |
| **Best G base cell** | **Forecast agreement w42 — robust SR 0.458** | beat its ablation and falsifier, missed the 1.0 floor |
| **Best valid development cell still** | **Topology migration w84 — robust SR 1.376** | Frontier-B; not cross-ranked against later snapshots |
| **Local Quantiacs access** | **`public_default`** | measured research does not wait for a personal API key |
| **Evidence stage** | **development only** | validation, recent diagnostics, official IS and uniqueness are untouched |

Frontier-G evidence is in [`evidence/frontier_20260911g`](https://github.com/Svyable/quantiacs-q25/tree/main/evidence/frontier_20260911g) with [PM report](https://github.com/Svyable/quantiacs-q25/blob/main/experiments/frontier_20260911g/pm_report.md). See the [full matrix](RESEARCH_MATRIX.md) for every valid/invalid cell and provenance.

---

## Campaign scoreboard

Later campaigns use the same hostile score — minimum Sharpe across 2016–2020 research and 2021–2022 development at 4%, 8%, and 12% ATR-linked slippage — but **separate sponsor snapshots**. Do not blend them into one leaderboard.

| Campaign | What was tested | Result | Best valid base |
|---|---|---|---|
| B | topology migration, liquidity hysteresis, shock recovery | topology survives development; hysteresis weak; shock unrepaired | `topology_migration_w84` **1.376** |
| C | signed risk, tail decay, assimilation | frozen / not a promotion lane | — |
| D | variance-ratio reversal, rank-transition reliability | `FALSIFIED_DEVELOPMENT`; rank term was allocator-erased | — |
| E | impact relief, range escape, response convexity | `FALSIFIED_DEVELOPMENT` | — |
| F | signed triangles, weekly posterior, expert/cash policy | `FALSIFIED_DEVELOPMENT`; posterior 0.944 lost to pooled ablation | — |
| **G** | edge uncertainty, forecast agreement, cost-relative persistence | agreement `KILL_WEAK_ALPHA` 0.458; other two `FALSIFIED_DEVELOPMENT` | none ≥ 1.0 |

### Frontier-G development ranking

| Dev rank | Candidate | Mechanism | Robust SR | Research SR @12% | Dev SR @12% | Worst DD @12% |
|---:|---|---|---:|---:|---:|---:|
| 1 | `persistent_low_vol` | generic control | 0.641 | 1.495 | 0.641 | -93.3% |
| 2 | **`forecast_agreement_w42`** | slow/fast residual rank agreement | **0.458** | **1.064** | **0.458** | -79.5% |
| 3 | `equal_liquid` | generic control | 0.270 | 1.436 | 0.270 | -93.6% |
| 4 | `forecast_agreement_ablation` | slow residual only | 0.255 | 0.968 | 0.255 | -67.1% |
| 5 | `forecast_agreement_w63` | same family, longer memory | 0.213 | 1.034 | 0.213 | -73.7% |

### What Frontier-G says

**Forecast agreement is a real mechanism and a weak book.** The 42-day parent beat the slow-only ablation (0.255) and the disagreement falsifier (−0.134). That is the opposite of Frontier-F's weekly posterior, whose market-state condition lost to pooling. It still missed the 1.0 floor, correlated 0.859 with equal-liquid, and carried −79.5% stressed drawdown. Keep the formula frozen. Do not search nearby windows.

**Residual-edge uncertainty change failed.** Every change-based window was negative; the level-only ablation scored 0.116. Do not invert the change sign. This does not touch Frontier-B topology migration, which remains the strongest valid development cell in an earlier snapshot.

**Cost-relative persistence failed.** All bases were negative and the no-ATR ablation beat the central parent. ATR scaling changed 86% of target days without earning its complexity.

**Topology migration w84 is still the development seam to press**, on its own evidence packet, not because G was weak. Drawdown is still too large for production, and one B neighbor failed integrity. Repair + forward test, not retune.

---

## Historical incumbent stack

The dated August-2026 roster remains a separate evidence lane. These values came from earlier research/execution-translation runs and are **not cross-ranked against the newer Frontier-B harness**.

| Frozen rank | Strategy | Full SR | Stress SR | Max DD | Role |
|---:|---|---:|---:|---:|---|
| 1 | **V10 Pareto** | **2.261** | **1.965 @12%** | -30.90% | legacy multi-factor / residual anchor |
| 2 | **V11 Balanced** | 1.261 | 0.899 @12% | -23.11% | event + lifecycle + motif core |
| 3 | **C165** | 1.230 | 0.934 @12% | -21.45% | consensus-risk efficiency |
| 4 | **V12 signed volume diffusion** | 1.035 | 0.750 @12% | -33.86% | structural volume→return network |
| 5 | **CoCrash126** | 1.772 | 1.627 @12% | -14.38% | crash-comovement defense |
| 6 | **Residual dispersion switch** | 1.536 | 1.410 @8% | -12.00% | sparse residual dispersion |
| 7 | **Breadth Thrust** | 1.185 | 1.075 @8% | -21.49% | breadth state timing |
| 8 | **Slow factor balance** | 1.526 | 1.445 @8% | -24.72% | defensive multi-factor |
| 9 | **Trend_hit126** | 1.700 | 1.538 @12% | -24.84% | persistent-trend reserve |
| 10 | **V5 latency** | 2.105 | 1.830 @12% | **-10.30%** | high-overlap V10-family reserve |

The old “top ten” is not ten independent alphas. Known aliases/near-aliases stay labeled so strategy-count theater cannot masquerade as diversification. The [Strategy Atlas](STRATEGY_ATLAS.md) contains the mechanism cards and overlap notes.

---

## The portfolio question

The target is not “highest Sharpe strategy.” The target is a small stack that survives:

`causality → exact Quantiacs evaluation → cost ladder → drawdown → turnover → destructive controls → residual/correlation diagnostics → untouched forward evidence → current platform checks`.

A candidate can improve the stack in at least four ways: add genuinely orthogonal residual return, reduce crash/drawdown exposure, improve cost/turnover efficiency, or act as a robust state/gross-risk controller. If it does none of those, a new filename is not a new strategy.

The frozen core still gives us a useful graph:

| | V10 | V11 | C165 | V12 |
|---|---:|---:|---:|---:|
| **V10** | 1.000 | 0.288 | 0.329 | 0.398 |
| **V11** | 0.288 | 1.000 | 0.334 | 0.414 |
| **C165** | 0.329 | 0.334 | 1.000 | 0.281 |
| **V12** | 0.398 | 0.414 | 0.281 | 1.000 |

These are historical matched-stream diagnostics through 2026-08-20, not authenticated Quantiacs uniqueness clearance.

---

## Dogfood methodology

Every new strategy is supposed to create the same evidence packet it will later be judged by. The harness now separates three things that used to get conflated:

| Dimension | Question |
|---|---|
| **Strategy quality** | did a valid return stream make money efficiently under hostile folds/costs? |
| **Evidence quality** | how comparable, complete, forward-safe and reproducible is the packet? |
| **Implementation health** | did source, causality, liquidity, cleaner parity and replay checks pass? |

That distinction matters. A software assertion does not mean “Sharpe = 0,” and it does not automatically freeze every other preregistered cell in the family. Conversely, a clean implementation with a great development Sharpe still has **zero permission** to call itself validated.

The v2 packet adds robust fold/cost ranking, max drawdown, turnover, causality status, data/source hashes, access mode and explicit failure stage. Exact Quantiacs return streams also carry CAGR, Sortino, Calmar and hit-rate diagnostics. The public matrix is generated from canonical evidence rather than hand-edited screenshots.

[Read the evidence model →](EVIDENCE_MODEL.md)

---

## Next research pressure

1. **Do not retune G.** Edge-uncertainty change, forecast-agreement windows, and ATR persistence stay frozen. The slow-only ablation is not a new winner.
2. **Topology follow-ups already preregistered before B returns were seen** — rank stability, fragmentation/recovery. Avoid tuning `topology_migration_w84` itself.
3. **Bring executable V10/C165/V12 controls into the current harness** so residual tests stop using only generic equal-liquid / inverse-vol / low-vol baselines.
4. **Opportunity-density cash gates and unrepaired B shock-recovery cells** remain open, as implementation repairs rather than grid searches.

The research agent contract remains **24 hypotheses → score before returns → preregister 6 → implement at most 3 → falsify aggressively**.

---

## Machine-readable surface

The dashboard has a generated data endpoint at [`data/strategy_matrix.json`](data/strategy_matrix.json). The observed Frontier-B source snapshot lives in the repository under `evidence/frontier_20260910b/observed.json`. Historical incumbents remain in `configs/historical_top10.yaml`.

Missing evidence stays missing. The site never copies metrics from a related implementation or converts a failed run into a number.

---

## Status legend

**Historical frozen** — dated earlier evidence, useful as incumbent context.  
**Development observed** — exact research/dev run; rankable only inside the comparable lane.  
**Repair invalid cells** — promising mechanism plus software/integrity debt.  
**Kill weak alpha** — valid base cells fail the predefined development floor.  
**Falsified development** — destructive control matches/beats the parent.  
**PENDING** — no attached measured packet.  
**Authenticated preclear** — participant-bound correlation/precheck completed.

The goal is to arrive at October with a small set of **causal, distinct, cost-aware mechanisms that have survived serious attempts to kill them**.
