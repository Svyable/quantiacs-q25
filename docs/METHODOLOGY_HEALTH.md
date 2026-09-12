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
| Dashboard index includes latest | **no** |

The detailed matrix and this health surface intentionally have different evidence tiers. A summary-only campaign is shown here rather than silently inventing matrix rows that were never committed.

## Latest-campaign family triage

This ordering is valid **only inside the latest campaign**. Families first have to clear the fixed robust-development floor; ties are then ordered by measured robust Sharpe. No weighted mega-score is used.

| Rank | Family | Best base | Robust SR | Floor ≥1.0 | Decision | Central | Ablation | Falsifier |
|---:|---|---|---:|---:|---|---:|---:|---:|
| 1 | `spectral_diversification_gate` | `spectral_diversification_gate_w42` | 0.786 | FAIL | `FALSIFIED_DEVELOPMENT` | — | — | — |
| 2 | `positive_edge_shedding` | `positive_edge_shedding_w63` | 0.752 | FAIL | `FALSIFIED_DEVELOPMENT` | 0.752 | — | — |
| 3 | `spectral_residual_momentum` | `spectral_residual_momentum_w63` | 0.667 | FAIL | `KILL_WEAK_ALPHA` | 0.667 | — | — |

## Surviving development seam

The most recent structured packet that names a survivor identifies **`topology_migration_w84`** with reported robust-development Sharpe **1.376**. Structured declaration from `frontier_20260912i`.

> Earlier Frontier-B development evidence; not cross-validated here and not an official submission clearance.

## Dogfood checks

- **Recency is not rank.** The newest campaign can fail while an older, separately measured seam remains alive.
- **Evidence schemas are normalized, not guessed.** Known committed summary schemas map into one control surface; absent metrics remain absent.
- **No cross-campaign scalar.** Sponsor snapshots and evidence stages stay separate; the renderer refuses to manufacture one global score.
- **Missing packets stay missing.** Summary-only evidence is labeled as such instead of being expanded into synthetic matrix rows.
- **CI is the freshness alarm.** Tests compare this renderer with checked-in JSON/Markdown, so new evidence makes the surface stale until regenerated.
- **Controls remain visible when structured.** Parent, ablation and falsifier metrics are displayed when the packet actually contains them.

## Current interpretation

Do not retune Frontier-J. topology_migration_w84 remains the only new-campaign family above the internal 1.0 robust-development floor; the next high-value action is a frozen forward/validation evaluation of that pre-existing survivor.

The next iteration should follow the latest packet's declared boundary and preregister any new mutation before return inspection.
