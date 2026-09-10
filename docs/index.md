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
| **Best valid Frontier-B base cell** | **Topology migration w84 — robust SR 1.376** | minimum Sharpe across research/dev × 4/8/12% ATR cost cells |
| **Topology w84 SR @ 12% ATR** | **1.376 research / 1.863 dev** | survives the harshest cost cell in both development folds |
| **Frontier-B implementation coverage** | **11 / 18 complete** | failed cells remain visible instead of becoming fake zeroes |
| **Local Quantiacs access** | **`public_default`** | measured research does not wait for a personal API key |
| **Evidence stage** | **development only** | validation, recent diagnostics, official IS and uniqueness are untouched |

The latest observed campaign came from GitHub Actions run **34437464861**, artifact **10136721138**, against an immutable data hash and preregistered manifest. See the [full matrix](RESEARCH_MATRIX.md) for every valid/invalid cell and provenance.

---

## Current development ranking

This is a **development lane**, not a contest leaderboard. The score is intentionally hostile: take the minimum Sharpe across the 2016–2020 research fold and 2021–2022 dev fold under 4%, 8%, and 12% ATR-linked slippage.

| Dev rank | Candidate | Mechanism | Robust SR | Research SR @12% | Dev SR @12% | Research DD @12% | Dev DD @12% |
|---:|---|---|---:|---:|---:|---:|---:|
| **1** | **`topology_migration_w84`** | residual-correlation topology migration | **1.376** | **1.376** | **1.863** | -46.3% | -26.7% |
| 2 | `topology_migration_w63` | same family, shorter memory | 1.080 | 1.205 | 1.080 | -51.1% | -53.4% |
| 3 | `liquidity_hysteresis_w21` | liquidity lifecycle / re-entry state | 0.333 | 1.062 | 0.333 | -52.0% | -51.8% |
| 4 | `liquidity_hysteresis_w42` | liquidity lifecycle / re-entry state | 0.333 | 1.062 | 0.333 | -52.0% | -51.8% |
| 5 | `liquidity_hysteresis_w63` | liquidity lifecycle / re-entry state | 0.333 | 1.062 | 0.333 | -52.0% | -51.8% |

### What the matrix says

**Topology migration is the seam to press.** Two valid base windows clear the internal 1.0 development floor. The w84 cell also beats its topology-destroying falsifier (robust SR 0.387) and its ablation (1.009) on the preregistered scalar score. But the drawdown is still too large to call this production-ready, and the w42 neighbor failed an integrity/software assertion. The correct next move is **repair + forward test**, not retune w84 until the screenshot gets prettier.

**Liquidity hysteresis is not a standalone alpha winner in this form.** All valid windows land at the same 0.333 robust score. Keep the lifecycle state as a possible conditioner for another mechanism; do not keep parameter-searching the same hypothesis.

**Shock recovery is unresolved, not secretly bad.** The base cells failed implementation/integrity in the captured artifact, so their economics are unknown. Repair only if the mechanism remains worth the engineering time.

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

1. **Topology follow-ups already preregistered before these returns were seen** — rank stability, fragmentation/recovery, and related topology-state hypotheses. Avoid tuning w84 itself.
2. **Repair invalid Frontier-B cells** only enough to establish whether the original frozen hypotheses work; no parameter expansion.
3. **Bring more incumbents into the exact current harness** so topology is compared against executable V10/C165/V12-quality controls rather than weak generic baselines.
4. **Press independent P1 seams** such as volatility term structure and online forecast surprise so a topology success does not turn the whole lab into a topology monoculture.

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
