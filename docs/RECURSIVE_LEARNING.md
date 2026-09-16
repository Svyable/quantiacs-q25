---
title: Recursive Learning
description: Temporal dogfood telemetry for whether the Q25 research loop is becoming more informative, falsifiable, and transferable.
---

# Q25 recursive learning telemetry

> No mega-score. No cross-campaign scalar ranking. These diagnostics measure the research process, not strategy quality.

## Recent campaign window

Window: **frontier_20260912k, frontier_20260912l, frontier_20260912m**.

| Campaign | Families | Falsification | Control support | Economic survival | Best robust SR | Median causal margin | Median Dev−Research SR |
|---|---:|---:|---:|---:|---:|---:|---:|
| `frontier_20260912k` | 3 | 3/3 (100.0%) | 1/3 (33.3%) | 0/3 (0.0%) | 0.782 | -0.083 | -0.783 |
| `frontier_20260912l` | 3 | 3/3 (100.0%) | 1/3 (33.3%) | 0/3 (0.0%) | 0.614 | -0.009 | -0.657 |
| `frontier_20260912m` | 3 | 3/3 (100.0%) | 0/3 (0.0%) | 0/3 (0.0%) | 0.307 | -0.655 | -0.623 |

## What the loop learned

- Falsification coverage: **9/9 (100.0%)**.
- Control-supported mechanisms: **2/9 (22.2%)**.
- Economic survivors: **0/9 (0.0%)**.
- Promotion-ready causal+economic intersections: **0/9 (0.0%)**.
- Families falsified by destructive controls: **7**.
- Control-supported but still economically weak families: **2**.
- Pooled median Dev−Research SR@12 gap across 27 comparable base cells: **-0.651**.
- Base cells with Dev SR@12 ≥ Research SR@12: **3/27**.

Exact family-name novelty is only a lexical breadth proxy; it is not semantic originality or contest-correlation evidence.

## Trajectory

- **best_robust_sharpe**: 0.782 → 0.307 (Δ -0.475; DOWN).
- **control_support_rate**: 0.333 → 0.000 (Δ -0.333; MIXED).
- **median_central_control_margin**: -0.083 → -0.655 (Δ -0.572; MIXED).
- **median_dev_minus_research_sharpe_12**: -0.783 → -0.623 (Δ 0.160; UP).

## Validation calibration

Observed frozen forward gates: **1**; failures: **1**; passes: **0**.
Median forward/development retention: **0.228**.
Median forward−development Sharpe delta: **-1.062**.

## Evidence debt

- Latest measured campaign: `frontier_20260912m`.
- Latest full matrix: `frontier_20260912k`.
- Measured campaigns since full matrix: **2**.
- Frozen measurement queue: **3**; next `frontier_20260912n`.

## State tags

- `FALSIFICATION_DISCIPLINE_STABLE`
- `ECONOMIC_FRONTIER_CONTRACTING`
- `CAUSAL_SUPPORT_WEAKENING`
- `RESEARCH_TO_DEV_OPTIMISM_PERSISTS`
- `PROMOTION_DROUGHT`
- `FORWARD_TRANSLATION_WEAK`

## Derived next actions

- **P1 MEASURE_FROZEN_QUEUE_FIRST** — A preregistered campaign is already frozen. Measure it unchanged before mutating hypotheses from newer diagnostics.
- **P2 DEEPEN_CANONICAL_MATRIX_EVIDENCE** — The measurement frontier is ahead of the latest full matrix; deepen evidence before the public surface drifts further.
- **P3 TREAT_RESEARCH_FOLD_HIGHS_AS_OPTIMISTIC** — Recent base cells have a negative pooled median Dev−Research Sharpe gap. Demand stability evidence before spending more research budget on research-fold leaders.
- **P4 CALIBRATE_DEVELOPMENT_CONFIDENCE** — Observed frozen forward validation retained only part of the development Sharpe. Keep development hits explicitly provisional.
- **P5 OPEN_DIFFERENT_OBJECT_CLASS_AFTER_QUEUE** — Recent best robust economics contracted across campaigns and no family reached the causal+economic intersection. After the frozen queue is measured, prefer a genuinely different alpha object over parameter rescue.

These actions are diagnostics derived from committed evidence. They do not rewrite frozen campaigns, reopen spent folds, or promote a strategy.
