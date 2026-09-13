---
title: Research Control Plane
description: Lane-separated strategy stack, evidence frontier, measurement queue, and dogfood diagnostics.
---

# Q25 research control plane

> This is a control plane, not a mega-score. Historical, development, forward-validation, and queued evidence stay in separate lanes.

## Canonical latest development campaign

**frontier_20260912l** · PROMOTE_ZERO · evidence `summary_only`

| Local rank | Family | Best base | Robust SR | Floor margin | Causal margin | Support | Decision |
|---:|---|---|---:|---:|---:|---|---|
| 1 | dollar_volume_share_migration | `dollar_volume_share_migration_w42` | 0.614 | -0.386 | 0.333 | PASS | KILL_WEAK_ALPHA |
| 2 | permutation_entropy_contraction | `permutation_entropy_contraction_w126` | 0.401 | -0.599 | -0.212 | FAIL | FALSIFIED_DEVELOPMENT |
| 3 | relative_value_convergence | `relative_value_convergence_w63` | 0.182 | -0.818 | -0.009 | FAIL | FALSIFIED_DEVELOPMENT |

## Frozen historical stack

Frozen roster order is preserved from its dated evidence. It is not cross-ranked against modern development packets.

| Frozen rank | Strategy | Role | Full SR | Stress SR | Max DD | Status |
|---:|---|---|---:|---:|---:|---|
| 1 | V10 multi-factor ensemble — Pareto | primary legacy core | 2.261 | 1.965 @ 12% ATR | -30.9% | prepare_precheck |
| 2 | V11 new-only event ensemble — Balanced | orthogonal event / lifecycle core | 1.261 | 0.899 @ 12% ATR | -23.1% | prepare_precheck |
| 3 | C165 mobility / consensus risk | risk-efficiency core | 1.230 | 0.934 @ 12% ATR | -21.4% | prepare_precheck |
| 4 | V12 signed volume diffusion — 50/50 bridge | structural volume/return network core | 1.035 | 0.750 @ 12% ATR | -33.9% | prepare_precheck_exact_official_gate_required |
| 5 | Co-crash shelter — base 126D | defensive crash-comovement sleeve | 1.772 | 1.627 @ 12% ATR | -14.4% | prepare_precheck |
| 6 | Residual dispersion switch | sparse dispersion-conditioned residual sleeve | 1.536 | 1.410 @ 8% ATR | -12.0% | prepare_precheck |
| 7 | Breadth Thrust Switch | market breadth acceleration timing | 1.185 | 1.075 @ 8% ATR | -21.5% | prepare_precheck |
| 8 | Slow defensive factor balance | multi-factor defensive balance | 1.526 | 1.445 @ 8% ATR | -24.7% | prepare_precheck |
| 9 | 126D positive-return consistency — five names | persistent trend reserve | 1.700 | 1.538 @ 12% ATR | -24.8% | conditional_reserve |
| 10 | V5 latency ensemble | low-risk alternative within the V10 family | 2.105 | 1.830 @ 12% ATR | -10.3% | conditional_reserve_high_overlap_with_v10 |

## Measurement frontier

| Campaign UID | Display label | State | Families | Cells | Measured decision |
|---|---|---|---:|---:|---|
| `frontier_20260912m` | Frontier-M | MEASURED_AWAITING_CANONICAL_INGEST | 3 | 15 | PROMOTE_ZERO_FREEZE_ALL |
| `frontier_20260913m` | Frontier-M | FROZEN_UNMEASURED_OR_UNRECEIPTED | 3 | 15 | — |

## Dogfood diagnostics

Pending canonical evidence ingestion: **1**. Frozen/unreceipted campaigns: **1**.

- **WARN Frontier-M collision:** `frontier_20260912m`, `frontier_20260913m`. Display full campaign UID; do not rename historical evidence.
- **P1 INGEST_MEASURED_EVIDENCE** `frontier_20260912m`: A successful benchmark receipt exists but canonical observed evidence is not committed.
- **P2 DISAMBIGUATE_FRONTIER_LABELS**: Multiple campaign IDs map to the same human Frontier label; preserve historical IDs but display full campaign UID.
- **P3 MEASURE_FROZEN_CAMPAIGN** `frontier_20260913m`: Frozen manifest is ahead of canonical evidence and has no committed measurement receipt.
- **P4 DEEPEN_MATRIX_EVIDENCE** `frontier_20260912l`: Latest committed campaign is not represented by a full canonical matrix packet.

## Reproducibility context

Latest replay-health packet: `frontier_20260912k` · **DECISION_STABLE_CONTEXT_DRIFT**. Decision-stable families: 3/3; max compared summary-metric delta: 0.000000006.

The control plane never averages metrics across provenance contexts.
