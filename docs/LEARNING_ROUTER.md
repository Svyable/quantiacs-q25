---
title: Learning Router
description: Evidence-stage router for recursive Q25 research work.
---

# Q25 learning router

> The router does not score strategies. It decides what type of research work is currently justified by committed evidence.

## Pipeline

- Canonical latest: `frontier_20260913o`.
- Measured awaiting canonical ingest: **1**.
- Frozen and still unmeasured: **0**.
- Failed frozen forward gates: **1**.
- Current bottleneck: **CANONICAL_INGEST** — Measured evidence exists but the canonical evidence frontier has not absorbed it yet.

## Belief updates

- **causal_yield · LOW_POSITIVE_YIELD** — 1/5 recent families beat matched destructive controls. _Development-only evidence; control support is not forward validation._
- **economic_yield · NO_RECENT_SURVIVORS** — 0/5 recent families clear the fixed robust-development floor. _The recent window is bounded and is not a claim about all historical strategies._
- **selection_transfer · RESEARCH_OPTIMISM_OBSERVED** — Median Dev−Research SR@12 is -1.729; 0/9 comparable cells held or improved. _This describes the recent comparable cells, not a universal shrinkage coefficient._
- **forward_translation · ONE_OBSERVED_FAILURE** — 1/1 observed frozen forward gates failed; retention 22.8%. _A single forward event is a calibration warning, not a population estimate._
- **evidence_freshness · CANONICAL_INGEST_BOTTLENECK** — Measured evidence exists but the canonical evidence frontier has not absorbed it yet. _Pipeline state is derived from committed repository artifacts only._

## Research-budget route

**Next:** `INGEST_MEASURED_EVIDENCE` `frontier_20260916p` — A successful benchmark receipt exists but canonical observed evidence is not committed.

Current-state backlog (recompute after the next evidence transition):
- `DEEPEN_MATRIX_EVIDENCE` `frontier_20260913o` — Latest committed campaign is not represented by a full canonical matrix packet.

New-hypothesis budget: **BLOCKED_BY_EXISTING_EVIDENCE_WORK** — Finish higher-priority ingestion / measurement / evidence-depth work before opening another mutable campaign.

Mutation guardrail: **Never retune a frozen or measured campaign to answer diagnostics produced by its own returns.**
