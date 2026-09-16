---
title: Recursive Learning
description: Temporal dogfood telemetry for whether the Q25 research loop is becoming more informative, falsifiable, and transferable.
---

# Q25 recursive learning telemetry

> No mega-score. No cross-campaign scalar ranking. These diagnostics measure the research process, not strategy quality.

## Recent campaign window

Window: **frontier_20260912n, frontier_20260913m, frontier_20260913o**.

| Campaign | Families | Falsification | Control support | Economic survival | Best robust SR | Median causal margin | Median Dev−Research SR |
|---|---:|---:|---:|---:|---:|---:|---:|
| `frontier_20260912n` | 1 | 1/1 (100.0%) | 0/1 (0.0%) | 0/1 (0.0%) | -0.676 | -0.261 | -1.806 |
| `frontier_20260913m` | 3 | 3/3 (100.0%) | 0/3 (0.0%) | 0/3 (0.0%) | -0.007 | -0.621 | -0.767 |
| `frontier_20260913o` | 1 | 1/1 (100.0%) | 1/1 (100.0%) | 0/1 (0.0%) | 0.171 | 0.110 | -1.757 |

## What the loop learned

- Falsification coverage: **5/5 (100.0%)**.
- Control-supported mechanisms: **1/5 (20.0%)**.
- Economic survivors: **0/5 (0.0%)**.
- Promotion-ready causal+economic intersections: **0/5 (0.0%)**.
- Families falsified by destructive controls: **4**.
- Control-supported but still economically weak families: **1**.
- Pooled median Dev−Research SR@12 gap across 9 comparable base cells: **-1.729**.
- Base cells with Dev SR@12 ≥ Research SR@12: **0/9**.

Exact family-name novelty is only a lexical breadth proxy; it is not semantic originality or contest-correlation evidence.

## Trajectory

- **best_robust_sharpe**: -0.676 → 0.171 (Δ 0.848; UP).
- **control_support_rate**: 0.000 → 1.000 (Δ 1.000; MIXED).
- **median_central_control_margin**: -0.261 → 0.110 (Δ 0.370; MIXED).
- **median_dev_minus_research_sharpe_12**: -1.806 → -1.757 (Δ 0.049; MIXED).

## Validation calibration

Observed frozen forward gates: **1**; failures: **1**; passes: **0**.
Median forward/development retention: **0.228**.
Median forward−development Sharpe delta: **-1.062**.

## Evidence debt

- Latest measured campaign: `frontier_20260913o`.
- Latest full matrix: `frontier_20260912k`.
- Measured campaigns since full matrix: **5**.
- Frozen measurement queue: **0**; next `—`.

## State tags

- `FALSIFICATION_DISCIPLINE_STABLE`
- `RESEARCH_TO_DEV_OPTIMISM_PERSISTS`
- `PROMOTION_DROUGHT`
- `FORWARD_TRANSLATION_WEAK`

## Derived next actions

- **P2 DEEPEN_CANONICAL_MATRIX_EVIDENCE** — The measurement frontier is ahead of the latest full matrix; deepen evidence before the public surface drifts further.
- **P3 TREAT_RESEARCH_FOLD_HIGHS_AS_OPTIMISTIC** — Recent base cells have a negative pooled median Dev−Research Sharpe gap. Demand stability evidence before spending more research budget on research-fold leaders.
- **P4 CALIBRATE_DEVELOPMENT_CONFIDENCE** — Observed frozen forward validation retained only part of the development Sharpe. Keep development hits explicitly provisional.

These actions are diagnostics derived from committed evidence. They do not rewrite frozen campaigns, reopen spent folds, or promote a strategy.
