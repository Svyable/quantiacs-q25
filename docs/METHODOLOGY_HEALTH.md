# Methodology Health

> Generated from committed evidence. This is a control surface for the research process, not a cross-campaign leaderboard.

## Evidence pulse

| Check | State |
|---|---|
| Latest measured campaign | `frontier_20260912i` |
| Latest evidence tier | `summary_only` |
| Latest campaign decision | `PROMOTE_ZERO_FREEZE_ALL` |
| Latest full matrix packet | `frontier_20260911h` |
| Detailed research matrix includes latest | **no — gap is explicit** |
| Dashboard index includes latest | **yes** |

The detailed matrix and this health surface intentionally have different evidence tiers. A summary-only campaign is shown here rather than silently inventing matrix rows that were never committed.

## Latest-campaign family triage

This ordering is valid **only inside the latest campaign**. Families first have to clear the fixed robust-development floor; ties are then ordered by measured robust Sharpe. No weighted mega-score is used.

| Rank | Family | Best base | Robust SR | Floor ≥1.0 | Decision | Central | Ablation | Falsifier |
|---:|---|---|---:|---:|---|---:|---:|---:|
| 1 | `partial_edge_entropy` | `partial_edge_entropy_w84` | 0.304 | FAIL | `KILL_WEAK_ALPHA` | 0.138 | 0.119 | 0.127 |
| 2 | `conditional_decoupling` | `conditional_decoupling_w84` | 0.288 | FAIL | `FALSIFIED_DEVELOPMENT` | 0.155 | 0.201 | 0.196 |
| 3 | `trend_dispersion_gate` | `trend_dispersion_gate_w42` | -0.358 | FAIL | `FALSIFIED_DEVELOPMENT` | -0.812 | 0.210 | 0.384 |

## Surviving development seam

The latest packet still identifies **`topology_migration_w84`** as the surviving new-alpha seam, with a reported robust-development Sharpe of **1.376** in its earlier evidence packet.

> Earlier Frontier-B development evidence; not cross-validated here and not an official submission clearance.

## Dogfood checks

- **Recency is not rank.** The newest campaign can fail while an older, separately measured seam remains alive.
- **No cross-campaign scalar.** Sponsor snapshots and evidence stages stay separate; the renderer refuses to manufacture one global score.
- **Missing packets stay missing.** Summary-only evidence is labeled as such instead of being expanded into synthetic matrix rows.
- **CI is the freshness alarm.** Tests compare this renderer with the checked-in JSON/Markdown, so the next committed campaign makes the surface stale until it is regenerated.
- **Controls remain visible.** Parent, ablation and falsifier results sit beside the family rank so a high number cannot hide failed causality/economic controls.

## Current interpretation

Changing from marginal residual-correlation topology to shrinkage partial-correlation topology did not reproduce the topology-migration edge. The non-topology residual-trend dispersion expansion gate was harmful. Preserve these as negative evidence and do not tune or invert after observation.

The next iteration should attack the surviving seam with preregistered, causally distinct repairs and forward-safe diagnostics—not tune the latest failed families after observation.
