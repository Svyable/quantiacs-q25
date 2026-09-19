---
title: Submission Readiness
description: Evidence-backed operational readiness of exact frozen Q25 submission artifacts.
---

# Q25 submission readiness

> This is not a strategy ranking. It separates packaging, full-history economics, frozen forward confidence, public/default correlation smoke, and participant/account-bound uniqueness clearance.

Packaged artifacts: **2/3** · full-history 4%-ATR floor pass: **3/3** · frozen forward observed: **1** · public smoke clear: **2** · account-bound clear: **0**.

| Candidate | Stage | Artifact | Full SR @4% | SR @10% | SR @12% | Frozen forward @4% | Public smoke | Remaining blockers |
|---|---|---|---:|---:|---:|---:|---|---|
| **Sharpe7 Vol2** | `PROMOTED_FORWARD_PASS_PENDING_ACCOUNT_BOUND_CORRELATION` | yes | 1.834 | 1.508 | 1.400 | 1.499 | `PUBLIC_DEFAULT_CLEAR` | ACCOUNT_BOUND_UNIQUENESS_CORRELATION |
| **SOTA Meta** | `PROMOTED_PENDING_FORWARD_AND_ACCOUNT_BOUND_CORRELATION` | yes | 1.347 | — | 1.070 | — | `PUBLIC_DEFAULT_CLEAR` | FROZEN_FORWARD_CONFIDENCE_NOT_MEASURED, ACCOUNT_BOUND_UNIQUENESS_CORRELATION |
| **Lattice Consensus** | `QUALIFIED_SOURCE_NOT_PACKAGED` | no | 1.460 | — | 1.056 | — | `NOT_RUN` | PACKAGE_EXACT_MULTIPASS_ARTIFACT |

## Hard boundary

Participant/account-bound uniqueness correlation must be run on the exact final artifact before treating public smoke as contest clearance.

A clean public/default correlation response with `PARTICIPANT_ID=0` is useful smoke evidence, but it is **not** account-bound uniqueness clearance.
