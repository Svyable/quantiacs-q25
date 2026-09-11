# Frontier-G: edge uncertainty, forecast agreement and cost-relative persistence

**Decision: freeze all three tested approaches; promote zero.** All 18 objects completed exact Quantiacs evaluation after a pre-measurement coordinate-order repair in the agreement family. Forecast agreement was the only family whose defining controls lost to the parent, but every base window missed the 1.0 robust-Sharpe floor. Residual-edge uncertainty change and cost-relative persistence were frozen as `FALSIFIED_DEVELOPMENT`. No later chronological window was opened.

This campaign follows the merged Frontier-F PR. It changes the research object rather than extending a failed parameter grid: graph *uncertainty* rather than signed-triangle balance change, two-speed forecast *agreement* rather than a market-state weekly posterior, and cost-relative residual persistence rather than a teacher-proxy allocation policy.

## Frozen hypotheses

| Approach | Mechanism | Ablation | Destructive control |
|---|---|---|---|
| Residual-edge uncertainty | 21-day change in the standard deviation of residual-correlation edges, gated on a positive 21-day residual trend | Current uncertainty level with the same residual-trend gate | Rotate uncertainty-change across eligible identities |
| Two-speed forecast agreement | Rank agreement between a W-day residual mean and a fully realized 7-day residual mean, requiring both positive | Slow residual mean only | Keep both-positive gate but score disagreement |
| Cost-relative persistence | Persistent W-day residual edge scaled by own 14-day relative ATR | Persistent residual edge without ATR | Pair each asset with another eligible name's relative ATR |

All three allocate bounded confidence directly to at most five names, at most 20% each; unused capital remains cash. Monday entries and persistent eligibility exits apply throughout. Graph and cost windows are 42/63/84 days; agreement windows are 21/42/63. No market-timing gate was added after measurement.

A first measurement attempt failed integrity on agreement bases because rank arithmetic reordered asset coordinates on the real ticker set. The repair reindexes scores to the input asset order. It does not change windows, top-K, or the economic formula. Synthetic tests with alphabetically ordered labels did not catch this; an unsorted-label test was added before rerunning.

## Registration and provenance

24 hypotheses were scored, six preregistered and three implemented. The three unimplemented registrations remain untested. The frozen grid contains nine base variants and six matched ablations/falsifiers, plus three generic controls. All A–F development history is already observed; neither repeated development nor the predeclared bootstrap is a fresh holdout.

Implementation freeze hashes are in `implementation_freeze.json`. [source.json](../../evidence/frontier_20260911g/source.json) records toolbox, dependency and data provenance. Public/default sponsor data were used, with no outside substitute. The sponsor snapshot hash differs from Frontier-F; do not cross-rank the two packets.

## Exact development results

Robust Sharpe is the minimum across 2016–2020 research and 2021–2022 development at 4%, 8% and 12% ATR-linked slippage. The complete zero/4/8/12 cost ladder, CAGR, Sortino, Calmar, hit rate, drawdown and turnover remain in the individual records. These are local historical measurements.

| Cell | Mode | Robust SR | Research SR, 12% | Dev SR, 12% | Worst DD, 12% |
|---|---|---:|---:|---:|---:|
| persistent_low_vol | control | 0.641 | 1.495 | 0.641 | -93.3% |
| forecast_agreement_w42 | base | 0.458 | 1.064 | 0.458 | -79.5% |
| equal_liquid | control | 0.270 | 1.436 | 0.270 | -93.6% |
| forecast_agreement_ablation | ablation | 0.255 | 0.968 | 0.255 | -67.1% |
| forecast_agreement_w63 | base | 0.213 | 1.034 | 0.213 | -73.7% |
| forecast_agreement_w21 | base | 0.145 | 1.292 | 0.145 | -76.8% |
| edge_uncertainty_ablation | ablation | 0.116 | 1.262 | 0.116 | -31.0% |
| inverse_vol_trend | control | 0.053 | 1.528 | 0.053 | -87.1% |
| cost_relative_persistence_w84 | base | -0.121 | 0.067 | -0.121 | -31.4% |
| cost_relative_persistence_w42 | base | -0.127 | 0.954 | -0.127 | -22.3% |
| forecast_agreement_falsifier | falsifier | -0.134 | 0.234 | -0.134 | -32.5% |
| cost_relative_persistence_ablation | ablation | -0.200 | 0.034 | -0.200 | -9.2% |
| edge_uncertainty_w84 | base | -0.208 | 0.532 | -0.208 | -3.1% |
| edge_uncertainty_w42 | base | -0.387 | 0.492 | -0.387 | -5.5% |
| cost_relative_persistence_w63 | base | -0.400 | 0.417 | -0.400 | -25.5% |
| cost_relative_persistence_falsifier | falsifier | -0.432 | 0.324 | -0.432 | -30.0% |
| edge_uncertainty_falsifier | falsifier | -0.552 | 0.732 | -0.552 | -4.6% |
| edge_uncertainty_w63 | base | -0.568 | 0.503 | -0.568 | -3.9% |

## Adjudication

**Forecast agreement:** the central 42-day window scored 0.458 and beat both the slow-only ablation (0.255) and the disagreement falsifier (−0.134). The other two windows were also positive versus the falsifier and also missed the 1.0 floor. Stressed drawdown was −79.5%. Correlation to the equal-liquid control was 0.859; the local residual Sharpe against generic controls was 0.945. That residual diagnostic is not uniqueness clearance and does not waive the floor. Preserve the formula. Do not widen the grid.

**Edge uncertainty:** every change-based window had negative development Sharpe. The central score was −0.568 versus 0.116 for the level-only ablation and −0.552 for shuffled identities. Rising residual-edge variance is not a useful leadership score in this implementation. This does not license inverting the change sign after seeing returns, and it does not falsify Frontier-B topology migration.

**Cost-relative persistence:** all three base windows were negative. The central 63-day score of −0.400 lost to the no-ATR ablation (−0.200). Pairing each name with another asset's ATR was weaker still (−0.432). ATR scaling changed capital, but not in a way that earned its complexity. Do not turn the ablation into a winner.

No base window reached 1.0. The frozen rule therefore did not trigger the extra execution-day test or the already contaminated 2023–2024 diagnostic. No 2025+, live-window or account submission action occurred.

## Do the mechanisms change capital?

The following compares each matched central parent and control. Target differences cover all 2,922 input days including warm-up. Return differences use 2021–2022 net returns at 4% ATR costs and 2,000 circular 21-day block resamples with a predeclared seed. Intervals are annualized arithmetic percentage-point differences, not CAGR or multiple-testing-adjusted confidence.

| Parent | Control | Changed target days | Annualized return difference | 95% block interval |
|---|---|---:|---:|---|
| edge_uncertainty_w63 | edge_uncertainty_ablation | 97.0% | −7.67 pp | [−31.15, 15.32] pp |
| edge_uncertainty_w63 | edge_uncertainty_falsifier | 89.8% | +0.05 pp | [−0.89, 1.02] pp |
| forecast_agreement_w42 | forecast_agreement_ablation | 98.4% | +17.72 pp | [−9.25, 46.39] pp |
| forecast_agreement_w42 | forecast_agreement_falsifier | 94.3% | +37.67 pp | [−18.59, 94.21] pp |
| cost_relative_persistence_w63 | cost_relative_persistence_ablation | 86.2% | −1.89 pp | [−15.28, 13.04] pp |
| cost_relative_persistence_w63 | cost_relative_persistence_falsifier | 86.2% | −0.08 pp | [−3.53, 3.76] pp |

All six pairs produce distinct target paths, so this campaign does not repeat Frontier-D's erased ordinal sizing interaction. Wide block intervals and the repeatedly inspected development sample limit inference. The repository freeze decisions are operational rules, not statistical proof that an economic idea can never work.

## Implementation and evidence health

- 41 new premeasurement tests passed, including unsorted-label coordinate order, prefix causality, 365-day replay, asset-order invariance, future-asset exclusion, edge-uncertainty arithmetic, agreement rank logic and ATR density monotonicity.
- All 18 measured objects completed exact evaluation and passed seven real-data prefix checkpoints. Cleaner diagnostics are retained per candidate.
- Dashboard, compile and diff checks are required after this packet is committed.
- Candidate packets retain exact parameters, registration/source/data/toolbox hashes, runtime, causality, cleaner changes and evidence stage.
- Historical V10/V11/V12 matched streams and authenticated platform uniqueness remain PENDING; the generic-control regression is research-trained and evaluated on development.

## Next research boundary

Keep these formulas and parameter grids frozen. Do not invert edge-uncertainty change, promote the slow-only agreement ablation, or drop ATR after seeing that the cost term hurt. A subsequent campaign could preregister a topology *rank-stability* object that is still unimplemented from Frontier-B, an opportunity-density cash gate that does not rank names, or bring an executable V10/C165/V12 control into the current harness so residual tests are no longer generic. Those are untested proposals and inherit no performance from this campaign.

## Reproduce

The dedicated `frontier-g-alpha-benchmark` workflow installs the frozen toolbox and core numerical dependency versions, runs the complete test suite, measures the campaign and attaches mechanism diagnostics. Preserve a new sponsor snapshot under its new data hash.

```bash
API_KEY=default python -m research.iteration \
  --manifest experiments/frontier_20260911g/manifest.json \
  --output results/frontier_20260911g --budget 18
python -m pytest -q tests
python scripts/build_research_dashboard.py --check
```
