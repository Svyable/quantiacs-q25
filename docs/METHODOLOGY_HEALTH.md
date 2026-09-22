# Methodology Health

> Generated from committed evidence. This is a recursive feedback surface for the research process, not a cross-campaign leaderboard or an optimization score.

## Evidence pulse

| Check | State |
|---|---|
| Latest measured campaign | `frontier_20260916p` |
| Latest evidence tier | `summary_only` |
| Latest campaign decision | `PROMOTE_ZERO` |
| Latest full matrix packet | `frontier_20260912k` |
| Measured campaigns since full matrix | **6** |
| Homepage bound to generated health JSON | **yes** |
| Detailed research matrix includes latest | **no — evidence-depth gap is explicit** |

## Recursive learning telemetry

These metrics are a **vector, not a score**. They are intended to make the next research action more informative while resisting reward hacking.

| Feedback channel | Latest state | What it means |
|---|---:|---|
| Falsification coverage | **1/1 (100%)** | families with central + ablation + destructive falsifier measurements |
| Causal support | **0/1 (0%)** | central parent beats both matched destructive controls |
| Economic survival | **0/1 (0%)** | best base clears the fixed robust-development floor |
| Promotion-ready intersection | **0/1 (0%)** | clears the floor **and** survives controls; still not validation |
| Decision resolution | **1/1 (100%)** | measured families ended with an explicit decision code |
| Best floor margin | **-2.354** | best latest-family robust SR minus the fixed 1.0 floor |
| Median central-vs-control margin | **-1.257** | positive is causal support; negative means a control matched/beat the parent |

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
| 1 | `liquidity_requalification_hysteresis` | `liquidity_requalification_hysteresis_w84` | -1.354 | -2.354 | -1.432 | -0.175 | -1.257 | FAIL | `FALSIFIED_DEVELOPMENT` |

## Dogfood checks

- **Newer evidence can invalidate older prose.** Forward-validation packets are reconciled against development-leader claims before rendering.
- **Unmeasured work is visible but cannot masquerade as evidence.** Preregistered manifests ahead of the latest measured campaign appear only in the measurement queue.
- **No cross-campaign scalar.** Strategy quality, causal support, validation state, evidence depth and queue state remain separate feedback channels.
- **Missing packets stay missing.** Summary-only evidence is labeled as such instead of being expanded into synthetic matrix rows.
- **CI remains the freshness alarm.** Tests compare this renderer with checked-in JSON/Markdown; the homepage reads the generated JSON directly.

## Latest measured interpretation

Frontier-P measured the preregistered historical-liquidity requalification-hysteresis mechanism on the reused 2016-2022 development surface. None of the three base windows survived development: research/dev SR@12% was -0.154/-1.719 for w42, 0.174/-1.432 for w63, and 0.751/-1.354 for w84. The central 63-day parent was also beaten by both preregistered destructive controls: the no-history ablation reached -0.175 and the rotated eligibility-state falsifier -0.998. The mechanism is therefore FALSIFIED_DEVELOPMENT, not merely weak. Promote zero. Do not invert, retune, grid-rescue, or reopen 2023-2024.
