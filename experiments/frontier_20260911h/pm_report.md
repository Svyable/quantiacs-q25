# Frontier-H: clustering escape, factor-loading escape, neighbor identity

**Decision: freeze all three tested approaches; promote zero.** All 18 objects completed exact Quantiacs evaluation. Every implemented family failed its predeclared ablation or identity-rotation control. The strongest object in the packet is the neighbor-churn *ablation* (static isolation) at robust Sharpe 0.884. That is a control, not a qualified alpha, and it is not promoted.

This campaign follows merged Frontier-F. It does not retune unsigned centrality migration. It tests three different residual-graph objects on the only new-campaign seam that previously cleared the internal development floor (`topology_migration_w84` robust SR 1.376).

## Frozen hypotheses

| Approach | Mechanism | Ablation | Destructive control |
|---|---|---|---|
| Clustering escape | Falling Onnela weighted clustering of \|residual corr\| during mean-\|corr\| fragmentation, with positive residual trend | Current low clustering with the same gates | Rotate clustering-change across eligible identities |
| Factor-loading escape | Falling absolute loading on the leading residual-corr eigenvector during spectral-gap compression, with positive residual trend | Current low leading loading with the same gates | Rotate loading-change across eligible identities |
| Neighbor-identity churn | Jaccard turnover of each name's top-3 residual neighbors, with positive residual trend and no global fragmentation gate | Static isolation (low mean \|corr\|) with the same residual-trend gate | Rotate churn scores across eligible identities |

All three allocate bounded confidence to at most five names, at most 25% each; unused capital remains cash. Monday entries and persistent eligibility exits apply throughout. Windows are 42/63/84 days. No market-timing gate was added after measurement.

## Registration and provenance

24 hypotheses were scored, six preregistered and three implemented. The three unimplemented registrations (spectral-gap cash, bridge betweenness, failed-recovery count) remain untested. The frozen grid contains nine base variants and six matched ablations/falsifiers, plus three generic controls. All A–F development history is already observed; neither repeated development nor the predeclared bootstrap is a fresh holdout.

Implementation hashes were frozen in `implementation_freeze.json` before any H return was inspected. Git freeze commit: `3ae673a`. File hashes are in `implementation_freeze.json`; [source.json](../../evidence/frontier_20260911h/source.json) records toolbox, dependency and data provenance. Public/default sponsor data were used, with no outside substitute.

## Exact development results

Robust Sharpe is the minimum across 2016–2020 research and 2021–2022 development at 4%, 8% and 12% ATR-linked slippage. The complete zero/4/8/12 cost ladder, CAGR, Sortino, Calmar, hit rate, drawdown and turnover remain in the individual records. These are local historical measurements.

| Cell | Mode | Robust SR | Research SR, 12% | Dev SR, 12% | Worst DD, 12% |
|---|---|---:|---:|---:|---:|
| neighbor_identity_churn_ablation | ablation | 0.884 | 1.315 | 0.884 | -69.8% |
| persistent_low_vol | control | 0.641 | 1.495 | 0.641 | -93.3% |
| clustering_escape_ablation | ablation | 0.558 | 0.558 | 1.436 | -2.2% |
| neighbor_identity_churn_falsifier | falsifier | 0.448 | 1.286 | 0.448 | -47.5% |
| factor_loading_escape_w84 | base | 0.401 | 0.580 | 0.401 | -0.3% |
| clustering_escape_w84 | base | 0.385 | 0.981 | 0.385 | -0.1% |
| neighbor_identity_churn_w84 | base | 0.341 | 1.125 | 0.341 | -50.2% |
| neighbor_identity_churn_w63 | base | 0.320 | 1.183 | 0.320 | -55.9% |
| neighbor_identity_churn_w42 | base | 0.282 | 1.177 | 0.282 | -58.9% |
| equal_liquid | control | 0.270 | 1.436 | 0.270 | -93.6% |
| clustering_escape_falsifier | falsifier | 0.250 | 0.250 | 0.438 | -0.2% |
| factor_loading_escape_ablation | ablation | 0.095 | 0.095 | 1.045 | -4.6% |
| inverse_vol_trend | control | 0.053 | 1.528 | 0.053 | -87.1% |
| factor_loading_escape_falsifier | falsifier | 0.029 | 0.029 | 0.198 | -0.5% |
| clustering_escape_w63 | base | -0.065 | -0.065 | 1.493 | -0.2% |
| factor_loading_escape_w63 | base | -0.096 | -0.096 | 1.600 | -0.5% |
| clustering_escape_w42 | base | -0.244 | -0.244 | -0.232 | -1.6% |
| factor_loading_escape_w42 | base | -0.448 | -0.448 | 0.835 | -0.8% |

## Adjudication

**Neighbor-identity churn:** all three base windows had research Sharpe above 1.1 at 12% ATR costs and then failed development (0.282 to 0.341). The central 63-day model scored 0.320 versus 0.884 for static isolation and 0.448 for shuffled identities. The proposed turnover object lost to both controls. The ablation is correlated with equal-liquid (0.736) and persistent low-vol (0.726); its 0.851 residual Sharpe against generic controls does not make it a new family. Do not promote the ablation.

**Clustering escape:** the change-plus-fragmentation gate produced extremely sparse books (worst stressed drawdowns of -0.1% to -2.2%). The best base was 0.385. The central 63-day model scored -0.065 versus 0.558 for the current-level ablation. Identity rotation also beat the parent. Local clustering *change* is not a substitute for unsigned centrality *migration*. High residual Sharpes on these sparse books are cash-dominated diagnostics, not promotion evidence.

**Factor-loading escape:** the same sparsity pattern. The best base was 0.401 (84-day). The central 63-day model scored -0.096 versus 0.095 for the low-loading ablation. Leading-eigenvector loadings did not reproduce topology_migration. Do not invert the escape sign after seeing these numbers.

No base window reached 1.0, and every central mechanism failed a defining control. The frozen rule therefore did not trigger the extra execution-day test or the already contaminated 2023–2024 diagnostic. No 2025+, live-window or account submission action occurred.

## Do the mechanisms change capital?

The following compares each matched central parent and control. Target differences cover all 2,922 input days including warm-up. Return differences use 2021–2022 net returns at 4% ATR costs and 2,000 circular 21-day block resamples with a predeclared seed. Intervals are annualized arithmetic percentage-point differences, not CAGR or multiple-testing-adjusted confidence.

| Parent | Control | Changed target days | Annualized return difference | 95% block interval |
|---|---|---:|---:|---|
| clustering_escape_w63 | clustering_escape_ablation | 31.6% | -1.39 pp | [-2.72, -0.29] pp |
| clustering_escape_w63 | clustering_escape_falsifier | 31.4% | 0.05 pp | [0.01, 0.12] pp |
| factor_loading_escape_w63 | factor_loading_escape_ablation | 31.4% | -1.70 pp | [-4.58, 0.32] pp |
| factor_loading_escape_w63 | factor_loading_escape_falsifier | 31.4% | 0.26 pp | [0.06, 0.51] pp |
| neighbor_identity_churn_w63 | neighbor_identity_churn_ablation | 59.4% | -37.77 pp | [-80.34, -6.06] pp |
| neighbor_identity_churn_w63 | neighbor_identity_churn_falsifier | 55.8% | -4.53 pp | [-23.97, 19.19] pp |

The mechanisms change target paths, so this campaign does not repeat Frontier-D's erased ordinal sizing interaction. Neighbor churn versus static isolation is the only economically large contrast; it favors the ablation. Wide block intervals and the repeatedly inspected development sample limit inference. The repository freeze decisions are operational rules, not statistical proof that an economic idea can never work.

## Implementation and evidence health

- 40 new premeasurement tests passed: all modes and registered windows, prefix causality, 365-day replay, asset-order invariance, future-asset exclusion, Onnela clique arithmetic, leading-factor block structure and frozen-neighbor zero churn.
- All 18 measured objects completed exact evaluation and passed seven real-data prefix checkpoints.
- 229 tests passed in the freeze-time repository run; the evidence-linked suite is re-run after this packet is copied.
- Candidate packets retain exact parameters, registration/source/data/toolbox hashes, runtime, causality, cleaner changes and evidence stage.
- Historical V10/V11/V12 matched streams and authenticated platform uniqueness remain PENDING; the generic-control regression is research-trained and evaluated on development.

## Next research boundary

Keep these formulas and parameter grids frozen. Do not turn static isolation into a winner, invert clustering/loading escape, or widen the window grid. `topology_migration` remains the only new-campaign family above the internal floor; these three nearby objects did not reproduce it.

A subsequent campaign could (a) repair the invalid `topology_migration_w42` cell and forward-test the frozen w84 parent without changing its formula, or (b) preregister a *new* object that is not a 21-day change of another node statistic on the same residual-correlation matrix. Unimplemented H reserves inherit no performance from this packet.

## Reproduce

The dedicated `frontier-h-alpha-benchmark` workflow installs the frozen toolbox and core numerical dependency versions, runs the complete test suite, measures the campaign and attaches mechanism diagnostics. Preserve a new sponsor snapshot under its new data hash.

```bash
API_KEY=default python -m research.iteration \
  --manifest experiments/frontier_20260911h/manifest.json \
  --output results/frontier_20260911h --budget 18
python -m pytest -q tests
python scripts/build_research_dashboard.py --check
```
