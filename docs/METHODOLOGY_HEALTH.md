# Methodology Health

> Generated from committed evidence. This is a recursive feedback surface for the research process, not a cross-campaign leaderboard or an optimization score.

## Evidence pulse

| Check | State |
|---|---|
| Latest measured campaign | `frontier_20260912l` |
| Latest evidence tier | `summary_only` |
| Latest campaign decision | `PROMOTE_ZERO` |
| Latest full matrix packet | `frontier_20260912k` |
| Measured campaigns since full matrix | **1** |
| Homepage bound to generated health JSON | **yes** |
| Detailed research matrix includes latest | **no — evidence-depth gap is explicit** |

## Recursive learning telemetry

These metrics are a **vector, not a score**. They are intended to make the next research action more informative while resisting reward hacking.

| Feedback channel | Latest state | What it means |
|---|---:|---|
| Falsification coverage | **3/3 (100%)** | families with central + ablation + destructive falsifier measurements |
| Causal support | **1/3 (33%)** | central parent beats both matched destructive controls |
| Economic survival | **0/3 (0%)** | best base clears the fixed robust-development floor |
| Promotion-ready intersection | **0/3 (0%)** | clears the floor **and** survives controls; still not validation |
| Decision resolution | **3/3 (100%)** | measured families ended with an explicit decision code |
| Best floor margin | **-0.386** | best latest-family robust SR minus the fixed 1.0 floor |
| Median central-vs-control margin | **-0.009** | positive is causal support; negative means a control matched/beat the parent |

## Validation correction

The earlier development leader **`topology_migration_w84`** reported robust-development Sharpe **1.376**, but its frozen chronological validation is now observed.

- Forward gate: **`FAIL_FORWARD_GATE`**
- Forward Sharpe @ 12% ATR-linked cost: **0.314**
- Validation fold: **2023-01-01 → 2024-12-31**
- Fold state: **`SPENT_DO_NOT_MUTATE`**

## Measurement queue

The committed measurement frontier is ahead of the evidence frontier by **1 preregistered campaign(s)**.

Next frozen campaign: **`frontier_20260912m`** — 15 candidate/control cells across 3 families; automatic promotion is `False`.

Frontier-M is a preregistered OHLCV-only volatility-term-structure campaign. It pivots away from failed short-horizon Sharpe refinements and avoids simple inverse-vol or static low-vol claims; 2023-2024 is spent and excluded.

Until measured evidence is committed, this is a queue item—not a result. The useful recursive action is to measure or ingest the frozen packet unchanged, not mutate it because the dashboard is empty.

## Latest-campaign family triage

This ordering is valid **only inside the latest measured campaign**. Controls are shown beside economics so a high number cannot hide a broken causal story.

| Rank | Family | Best base | Robust SR | Floor margin | Central | Control ceiling | Causal margin | Support | Decision |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | `dollar_volume_share_migration` | `dollar_volume_share_migration_w42` | 0.614 | -0.386 | 0.614 | 0.281 | 0.333 | PASS | `KILL_WEAK_ALPHA` |
| 2 | `permutation_entropy_contraction` | `permutation_entropy_contraction_w126` | 0.401 | -0.599 | -0.046 | 0.166 | -0.212 | FAIL | `FALSIFIED_DEVELOPMENT` |
| 3 | `relative_value_convergence` | `relative_value_convergence_w63` | 0.182 | -0.818 | -0.024 | -0.015 | -0.009 | FAIL | `FALSIFIED_DEVELOPMENT` |

## Dogfood checks

- **Newer evidence can invalidate older prose.** Forward-validation packets are reconciled against development-leader claims before rendering.
- **Unmeasured work is visible but cannot masquerade as evidence.** Preregistered manifests ahead of the latest measured campaign appear only in the measurement queue.
- **No cross-campaign scalar.** Strategy quality, causal support, validation state, evidence depth and queue state remain separate feedback channels.
- **Missing packets stay missing.** Summary-only evidence is labeled as such instead of being expanded into synthetic matrix rows.
- **CI remains the freshness alarm.** Tests compare this renderer with checked-in JSON/Markdown; the homepage reads the generated JSON directly.

## Latest measured interpretation

Frontier-L measured three preregistered non-graph families on the reused 2016-2022 development surface. Dollar-volume share migration is the strongest new base family at robust Sharpe 0.614 and its central 42-day parent beats both matched controls, but every base window remains below the fixed 1.0 development floor (KILL_WEAK_ALPHA). Permutation-entropy contraction and relative-value convergence are FALSIFIED_DEVELOPMENT by their preregistered destructive controls/ablations. Promote zero. Do not grid-rescue. 2023-2024 remains spent and was excluded.
