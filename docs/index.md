---
title: Q25 Quantitative Research Lab
description: Evidence-aware crypto alpha research for Quantiacs Q25 — causal mechanisms, measured development packets, and an auditable strategy stack.
---

# Q25 Quantitative Research Lab

> **Build mechanisms. Measure them with the same harness. Keep failures visible.**

This is the public control surface for the Quantiacs Q25 Crypto Top-10 Long program. The repository is the evidence source of truth; this site keeps four questions separate instead of collapsing them into one fake score:

1. what is the latest measured experiment,
2. what survived its destructive controls,
3. what strategy seam is still alive,
4. how fresh and complete is the evidence surface itself.

[**Methodology Health**](METHODOLOGY_HEALTH.md) · [Research Matrix](RESEARCH_MATRIX.md) · [Strategy Atlas](STRATEGY_ATLAS.md) · [Evidence Model](EVIDENCE_MODEL.md) · [Research Method](RESEARCH_METHOD.md) · [Testing Pyramid](TESTING_PYRAMID.md) · [Agent Playbook](STRATEGY_GENERATION_PLAYBOOK.md)

---

## Lab pulse

| Current object | State | Why it matters |
|---|---:|---|
| **Latest measured campaign** | **`frontier_20260912j` — promote zero / freeze all** | 18/18 declared objects completed; recency is not rank |
| **Best Frontier-J base family** | **spectral-diversification gate w42 — robust SR 0.786** | interesting local economics, but below the fixed 1.0 floor and the central gate loses to its ablation |
| **Surviving new-alpha seam** | **`topology_migration_w84` — robust development SR 1.376** | still the only new-campaign family above the internal development floor |
| **Latest full matrix packet** | **Frontier-H** | J is summary-only; that evidence-tier gap is displayed rather than hidden |
| **Evidence stage** | **development only** | the selected topology survivor has not yet earned chronological forward evidence or participant-bound clearance |

Frontier-J evidence is frozen in [`evidence/frontier_20260912j`](https://github.com/Svyable/quantiacs-q25/tree/main/evidence/frontier_20260912j). The generated [Methodology Health](METHODOLOGY_HEALTH.md) surface scans committed evidence and makes dashboard lag an explicit CI-visible state.

---

## Development stack: rank only where comparison is legitimate

There is **no global cross-campaign leaderboard**. Sponsor snapshots, evidence stages and harness generations are not silently blended. The stack is shown as evidence lanes.

### Lane A — surviving new-alpha seam

| Status | Candidate | Source campaign | Robust development SR | Interpretation |
|---|---|---|---:|---|
| **forward-test** | `topology_migration_w84` | Frontier-B | **1.376** | only new-campaign family still above the internal 1.0 robust-development floor after A–J |

This remains research evidence, not submission clearance. The highest-value next action is the already-frozen chronological 2023–2024 validation of this exact selected strategy and family shape. The validation result may change confidence; it may not be used to switch windows or mutate the formula.

### Lane B — latest campaign triage (`frontier_20260912j`)

This ordering is valid only inside Frontier-J. Families first have to clear the fixed robust floor, then are ordered by measured robust Sharpe. No weighted mega-score.

| Rank | Family | Best base | Robust SR | Floor ≥1.0 | Decision |
|---:|---|---|---:|---:|---|
| 1 | spectral-diversification gate | `spectral_diversification_gate_w42` | **0.786** | FAIL | `FALSIFIED_DEVELOPMENT` |
| 2 | positive-edge shedding | `positive_edge_shedding_w63` | **0.752** | FAIL | `FALSIFIED_DEVELOPMENT` |
| 3 | spectral residual momentum | `spectral_residual_momentum_w63` | **0.667** | FAIL | `KILL_WEAK_ALPHA` |

The failures are informative. Positive-edge shedding looked strong only in the later development fold and lost to both its level ablation and identity-rotation control. The spectral gate's central parent lost to the no-gate ablation. Spectral residual momentum beat its matched controls but never cleared the 1.0 robust floor. These families stay frozen; none is inverted or threshold-tuned after observation.

### Lane C — frozen historical incumbents

The dated August-2026 roster remains useful context, but it is **not cross-ranked against the newer frontier harness**.

| Frozen rank | Strategy | Full SR | Stress SR | Max DD | Role |
|---:|---|---:|---:|---:|---|
| 1 | **V10 Pareto** | **2.261** | **1.965 @12%** | -30.90% | legacy multi-factor / residual anchor |
| 2 | **V11 Balanced** | 1.261 | 0.899 @12% | -23.11% | event + lifecycle + motif core |
| 3 | **C165** | 1.230 | 0.934 @12% | -21.45% | consensus-risk efficiency |
| 4 | **V12 signed volume diffusion** | 1.035 | 0.750 @12% | -33.86% | structural volume→return network |
| 5 | **CoCrash126** | 1.772 | 1.627 @12% | -14.38% | crash-comovement defense |

Known aliases and near-aliases stay labeled in the [Strategy Atlas](STRATEGY_ATLAS.md), so strategy-count theater cannot masquerade as diversification.

---

## Campaign ledger

Later campaigns are experiments, not rungs on one leaderboard. A newer campaign may be more informative while producing worse strategies.

| Campaign | Research object | Outcome |
|---|---|---|
| B | topology migration, liquidity hysteresis, shock recovery | topology migration produced the surviving development seam |
| C–H | successive preregistered mechanism / falsification campaigns | see the [full Research Matrix](RESEARCH_MATRIX.md); failures and controls remain preserved |
| I | shrinkage partial-correlation conditional dependence + trend-dispersion opportunity | promote zero; all three families frozen |
| **J** | signed positive-edge shedding, spectral diversification state, leading-PC residual momentum | **18/18 complete; promote zero, freeze all three families** |

The sequence is increasingly specific: generic topology levels, clustering, neighbor churn, conditional dependence, signed-edge decomposition and spectral variants have not reproduced the original fragmentation-conditioned migration edge. That specificity is useful evidence, not a reason to retune the w84 lookback.

---

## Dogfood methodology

Every new strategy should create the same evidence packet it will later be judged by. The repo separates four dimensions:

| Dimension | Question |
|---|---|
| **Strategy quality** | did a valid return stream make money efficiently under hostile folds and costs? |
| **Evidence quality** | how comparable, complete, forward-safe and reproducible is the packet? |
| **Implementation health** | did source, causality, liquidity, cleaner and replay checks pass? |
| **Surface health** | does the dashboard include the newest committed evidence at the correct evidence tier? |

The methodology-health builder dogfoods this contract. It scans `evidence/frontier_*`, identifies the latest measured packet, labels summary-only versus full-matrix evidence, performs only within-campaign lexicographic triage, and emits checked-in JSON + Markdown. Tests compare the generated result to those artifacts, so a future campaign makes CI fail until the public surface is refreshed.

That distinction matters. A clean implementation with a great development Sharpe has **zero permission** to call itself validated. Likewise, a fresh experiment with weak returns does not displace an older surviving seam merely because it is newer.

[Read the methodology health surface →](METHODOLOGY_HEALTH.md)

---

## Portfolio question

The target is not “highest Sharpe strategy.” The target is a small stack that survives:

`causality → exact Quantiacs evaluation → cost ladder → drawdown → turnover → destructive controls → residual/correlation diagnostics → untouched forward evidence → current platform checks`.

A candidate can improve the stack by adding genuinely orthogonal residual return, reducing crash/drawdown exposure, improving cost/turnover efficiency, or acting as a robust state/gross-risk controller. If it does none of those, a new filename is not a new strategy.

Historical matched-stream diagnostics remain useful for diversification context, but they are not authenticated Quantiacs uniqueness clearance.

---

## Next research pressure

1. **Run the frozen topology-migration forward test before more development mutation.** `topology_migration_w84` was selected before validation; keep the w42/w63/w84 family, controls, costs and execution semantics unchanged.
2. **Do not rescue Frontier-J.** Signed-edge shedding, the chosen spectral gate and PC-residual momentum are measured negative evidence.
3. **Bring executable V10/C165/V12 controls into the current harness.** Generic equal-liquid / inverse-vol / low-vol controls are necessary but insufficient for portfolio-level incremental-alpha claims.
4. **If topology survives validation, move to portfolio admission evidence.** Compare matched return streams, drawdown overlap, turnover/cost attribution and participant-bound uniqueness rather than reopening development parameters.
5. **If topology fails validation, accept the failure.** Return to preregistered orthogonal primitives; do not window-switch on the validation fold.

The research-agent contract remains **24 hypotheses → score before returns → preregister 6 → implement at most 3 → falsify aggressively**.

---

## Machine-readable surfaces

- [`data/strategy_matrix.json`](data/strategy_matrix.json) — detailed generated matrix through the latest full matrix packet.
- [`data/methodology_health.json`](data/methodology_health.json) — latest-evidence, within-campaign triage and dashboard-health state.
- [`METHODOLOGY_HEALTH.md`](METHODOLOGY_HEALTH.md) — human-readable control surface generated from the same evidence scan.

Missing evidence stays missing. The site never copies metrics from a related implementation, fills a failed run with zero, or manufactures candidate rows from a summary packet.

---

## Status legend

**Historical frozen** — dated earlier evidence, useful as incumbent context.  
**Development observed** — exact research/dev run; rankable only inside the comparable lane.  
**Summary-only observed** — measured campaign with a committed summary but no full matrix packet.  
**Frozen forward validation** — selected before the chronological validation return is observed; parameters cannot change after the look.  
**Kill weak alpha** — valid base cells fail the predefined development floor.  
**Falsified development** — destructive control matches/beats the parent.  
**PENDING** — no attached measured packet.  
**Authenticated preclear** — participant-bound correlation/precheck completed.

The goal is to arrive at October with a small set of **causal, distinct, cost-aware mechanisms that have survived serious attempts to kill them**.
