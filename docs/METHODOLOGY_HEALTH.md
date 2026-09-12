# Methodology Health

> Generated from committed evidence. This is a control surface for the research process, not a cross-campaign leaderboard.

## Evidence pulse

| Check | State |
|---|---|
| Latest measured campaign | `frontier_20260912j` |
| Latest evidence tier | `summary_only` |
| Latest campaign decision | `PROMOTE_ZERO` |
| Latest full matrix packet | `frontier_20260911h` |
| Detailed research matrix includes latest | **no — gap is explicit** |
| Dashboard index includes latest | **yes** |

The detailed matrix and this health surface intentionally have different evidence tiers. A summary-only campaign is shown here rather than silently inventing matrix rows that were never committed.

## Latest-campaign family triage

This ordering is valid **only inside the latest campaign**. Families first have to clear the fixed robust-development floor; ties are then ordered by measured robust Sharpe. No weighted mega-score is used.

| Rank | Family | Best base | Robust SR | Floor ≥1.0 | Decision | Central | Ablation | Falsifier |
|---:|---|---|---:|---:|---|---:|---:|---:|
| 1 | `spectral_diversification_gate` | `spectral_diversification_gate_w42` | 0.786 | FAIL | `FALSIFIED_DEVELOPMENT` | 0.498 | 0.665 | 0.188 |
| 2 | `positive_edge_shedding` | `positive_edge_shedding_w63` | 0.752 | FAIL | `FALSIFIED_DEVELOPMENT` | 0.752 | 0.935 | 0.811 |
| 3 | `spectral_residual_momentum` | `spectral_residual_momentum_w63` | 0.667 | FAIL | `KILL_WEAK_ALPHA` | 0.667 | 0.487 | 0.254 |

## Surviving development seam

The latest packet still identifies **`topology_migration_w84`** as the surviving new-alpha seam, with a reported robust-development Sharpe of **1.376** in its earlier evidence packet.

> Earlier Frontier-B development evidence; not yet forward-validated here and not an official submission clearance.

## Dogfood checks

- **Recency is not rank.** The newest campaign can fail while an older, separately measured seam remains alive.
- **No cross-campaign scalar.** Sponsor snapshots and evidence stages stay separate; the renderer refuses to manufacture one global score.
- **Missing packets stay missing.** Summary-only evidence is labeled as such instead of being expanded into synthetic matrix rows.
- **CI is the freshness alarm.** Tests compare this renderer with the checked-in JSON/Markdown, so the next committed campaign makes the surface stale until it is regenerated.
- **Controls remain visible.** Parent, ablation and falsifier results sit beside the family rank so a high number cannot hide failed causality/economic controls.

## Current interpretation

Frontier-J changed the graph object rather than tuning topology_migration_w84. Signed positive-edge shedding, spectral diversification gating, and leading-PC residual momentum all failed their frozen development rules. Preserve them as negative evidence; topology_migration_w84 remains the only new-campaign family above the internal 1.0 robust-development floor and should face frozen chronological validation unchanged.

The next iteration should attack the surviving seam with preregistered, causally distinct repairs and forward-safe diagnostics—not tune the latest failed families after observation.
