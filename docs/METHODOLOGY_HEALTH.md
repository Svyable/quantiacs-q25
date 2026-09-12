# Methodology Health

> Generated from committed evidence. This is a recursive feedback surface for the research process, not a cross-campaign leaderboard or an optimization score.

## Evidence pulse

| Check | State |
|---|---|
| Latest measured campaign | `frontier_20260912k` |
| Latest evidence tier | `matrix_and_summary` |
| Latest campaign decision | `PROMOTE_ZERO` |
| Latest full matrix packet | `frontier_20260912k` |
| Measured campaigns since full matrix | **0** |
| Homepage bound to generated health JSON | **yes** |
| Detailed research matrix includes latest | **yes** |

## Recursive learning telemetry

These metrics are a **vector, not a score**. They are intended to make the next research action more informative while resisting reward hacking.

| Feedback channel | Latest state | What it means |
|---|---:|---|
| Falsification coverage | **3/3 (100%)** | families with central + ablation + destructive falsifier measurements |
| Causal support | **1/3 (33%)** | central parent beats both matched destructive controls |
| Economic survival | **0/3 (0%)** | best base clears the fixed robust-development floor |
| Promotion-ready intersection | **0/3 (0%)** | clears the floor **and** survives controls; still not validation |
| Decision resolution | **3/3 (100%)** | measured families ended with an explicit decision code |
| Best floor margin | **-0.218** | best latest-family robust SR minus the fixed 1.0 floor |
| Median central-vs-control margin | **-0.083** | positive is causal support; negative means a control matched/beat the parent |

## Validation correction

The earlier development leader **`topology_migration_w84`** reported robust-development Sharpe **1.376**, but its frozen chronological validation is now observed.

- Forward gate: **`FAIL_FORWARD_GATE`**
- Forward Sharpe @ 12% ATR-linked cost: **0.314**
- Validation fold: **2023-01-01 → 2024-12-31**
- Fold state: **`SPENT_DO_NOT_MUTATE`**

## Measurement queue

No preregistered campaign is currently ahead of the committed measurement frontier.

## Latest-campaign family triage

This ordering is valid **only inside the latest measured campaign**. Controls are shown beside economics so a high number cannot hide a broken causal story.

| Rank | Family | Best base | Robust SR | Floor margin | Central | Control ceiling | Causal margin | Support | Decision |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | `nearest_peer_detachment` | `nearest_peer_detachment_w63` | 0.782 | -0.218 | 0.782 | 0.701 | 0.081 | PASS | `KILL_WEAK_ALPHA` |
| 2 | `subspace_rotation_opportunity` | `subspace_rotation_opportunity_w42` | 0.354 | -0.646 | 0.332 | 0.415 | -0.083 | FAIL | `FALSIFIED_DEVELOPMENT` |
| 3 | `cohort_residual_divergence` | `cohort_residual_divergence_w63` | 0.131 | -0.869 | 0.131 | 0.241 | -0.110 | FAIL | `FALSIFIED_DEVELOPMENT` |

## Dogfood checks

- **Newer evidence can invalidate older prose.** Forward-validation packets are reconciled against development-leader claims before rendering.
- **Unmeasured work is visible but cannot masquerade as evidence.** Preregistered manifests ahead of the latest measured campaign appear only in the measurement queue.
- **No cross-campaign scalar.** Strategy quality, causal support, validation state, evidence depth and queue state remain separate feedback channels.
- **Missing packets stay missing.** Summary-only evidence is labeled as such instead of being expanded into synthetic matrix rows.
- **CI remains the freshness alarm.** Tests compare this renderer with checked-in JSON/Markdown; the homepage reads the generated JSON directly.

## Latest measured interpretation

Frontier-K measured three previously unmeasured reserves on the reused 2016-2022 development surface. Nearest-peer detachment is the strongest base at robust Sharpe 0.782 and beats both matched controls, but every window misses the 1.0 floor (KILL_WEAK_ALPHA). Subspace rotation and cohort residual divergence are FALSIFIED_DEVELOPMENT. Do not grid-rescue. 2023-2024 remains spent and was excluded. Topology_migration_w84 already failed its frozen forward gate (0.314); this campaign does not restore it.
