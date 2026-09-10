---
title: Evidence Model
description: How Q25 separates strategy quality, evidence quality, and implementation health.
---

# Evidence model

The lab tracks three independent dimensions. **Strategy quality** is the economic result of a valid observed return stream. **Evidence quality** is how complete, comparable, and forward-safe the measurement packet is. **Implementation health** is whether the code passed source, causality, liquidity, cleaner-parity, replay, and runtime checks.

A red implementation cell is not a bad Sharpe. It is **unknown economics because the implementation did not earn the right to be measured**. Likewise, a great development Sharpe is not “validated” merely because the implementation was clean.

## Evidence stages

| Stage | Meaning | May affect development ranking? | May be called contest-ready? |
|---|---|---:|---:|
| `PENDING` | code/hypothesis exists; no attached observed packet | no | no |
| `DEVELOPMENT_OBSERVED` | research/dev folds measured with exact local Quantiacs stats | yes, within the same campaign/harness | no |
| `VALIDATION_OBSERVED` | untouched chronological validation measured after freeze | yes, as forward evidence | no |
| `DIAGNOSTIC_OBSERVED` | later/recent segment inspected; never treated as pristine holdout afterward | context only | no |
| `LOCAL_POLICY_CLEARED` | causal, liquid, long-only, cleaner/replay, cost, DD, runtime and exact-IS gates passed locally | yes | no |
| `AUTHENTICATED_PRECLEAR` | participant-bound correlation/precheck completed | yes | not necessarily |
| `SUBMISSION_READY` | exact production artifact plus all current platform gates | final admission state | yes |

Historical roster entries are a separate `HISTORICAL_FROZEN` lane. They remain useful incumbents, but they are not silently cross-ranked against a newer harness.

## Required candidate packet

Every attempted cell should emit a machine-readable packet containing identity/provenance, status and failure stage, research/dev Sharpe at the full cost ladder, worst-fold/cost score, CAGR, Sortino, Calmar, max drawdown, turnover, causality result, data hash, source hashes, Quantiacs access mode, fold definitions, and destructive-control relationship where applicable.

The packet may contain missing values. Missing evidence stays missing. The dashboard never backfills, imputes, or copies a metric from another implementation.

## Family adjudication

Families are adjudicated only after independent preregistered cells have run. The harness must not freeze a whole family merely because one grid cell throws an exception.

A family can be:

- `NEEDS_FORWARD_EVIDENCE` — valid development evidence survives its destructive controls.
- `REPAIR_INVALID_CELLS_THEN_FORWARD` — promising valid evidence exists, but one or more preregistered cells failed software/integrity checks.
- `KILL_WEAK_ALPHA` — every valid base cell is below the predefined 1.0 development floor.
- `FALSIFIED_DEVELOPMENT` — a valid destructive control or ablation matches/beats its valid parent under the preregistered score.
- `INSUFFICIENT_VALID_EVIDENCE` — no valid base cell exists.

Those states are not promotion states. Validation, originality/correlation, current official IS, hosted multipass, runtime and account-bound checks are separate gates.

## Ranking rule

The current development rank uses the **minimum Sharpe across research and dev folds at 4%, 8%, and 12% ATR-linked slippage**. Ties break on worst drawdown, then turnover. The matrix also shows raw fold/cost metrics so the scalar score cannot hide pathologies.

A good rank is a prioritization device. The portfolio stack still cares about correlation, residual Sharpe, drawdown geometry, cost resilience, opportunity density, implementation simplicity and mechanism diversity.

## Dogfood rule

An agent that changes a strategy should run the same benchmark machinery used to criticize everyone else. “Looks causal” and “should perform” are not evidence. The default loop is:

`preregister → compile/test → API_KEY=default exact Quantiacs run → candidate packet → destructive controls → matrix → decision → only then forward evidence`.

If infrastructure is down, record `BLOCKED_INFRA`. Do not convert infrastructure failure into `PENDING_ALPHA`, and do not tune around it.

[Research matrix](RESEARCH_MATRIX.md) · [Testing pyramid](TESTING_PYRAMID.md) · [Research method](RESEARCH_METHOD.md)
