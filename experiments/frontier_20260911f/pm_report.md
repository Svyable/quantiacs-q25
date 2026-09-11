# Frontier-F: graph structure, probabilistic forecasting and allocation policy

**Decision: freeze all three tested approaches; promote zero.** All 18 objects completed exact Quantiacs evaluation. The weekly-payoff model was the strongest base at robust Sharpe 0.944, but removing its market-state conditioning beat the central model. Signed-triangle improvement and adaptive expert routing also failed their controls. No later chronological window was opened.

This campaign follows the merged Frontier-E PR. It changes the research object rather than extending a failed parameter grid: two discovery hypotheses and one explicitly classified allocation experiment. The latter overlaps existing V5/V10 routing and is not an independent alpha claim.

## Frozen hypotheses

| Approach | Mechanism | Ablation | Destructive control |
|---|---|---|---|
| Signed-triangle coherence | Change over 21 days in weighted balance of residual-correlation triangles, with positive own residual trend | Use current balance level without change | Rotate the change signal across eligible identities |
| Weekly-payoff posterior | Beta-smoothed win probability and shrunk gain/loss estimates from fully realized, nonoverlapping Monday-to-Monday labels, conditioned on the market state at forecast origin | Pool market states with the same readiness gate | Rotate realized payoffs across origin-eligible identities |
| Adaptive expert and cash policy | Downside-penalized exponential weights over fixed trend, defensive and cash experts | Equal thirds across experts | Swap trend and defensive utility labels, preserving cash |

Graph and posterior strategies allocate bounded confidence directly to at most five names, at most 20% each; unused capital remains cash. The policy combines two capped expert portfolios and a cash expert, so its union can contain more than five names while each asset remains at most 20%. Monday entries and persistent eligibility exits apply throughout. Graph windows are 42/63/84 days; posterior and policy windows are 84/126/168. No market timing gate was added after measurement.

The policy learns from an explicitly labeled close-to-close teacher proxy using previous-day expert weights. Those proxy returns are internal model inputs, not reported strategy performance. All candidate results below use exact Quantiacs execution and cost accounting.

## Registration and provenance

24 hypotheses were scored, six preregistered and three implemented. The three unimplemented registrations remain untested. The frozen grid contains nine base variants and six matched ablations/falsifiers, plus three generic controls. All A–E development history is already observed; neither repeated development nor the predeclared bootstrap is a fresh holdout.

GitHub preregistration commit: `acc448a73a1d697fe3df428feb88e38ae0c5505e`. Implementation freeze: `9b9c2bc864bb4d90274294f6198904afd951c39c`. Both were published before measurement. File hashes are in `implementation_freeze.json`; [source.json](../../evidence/frontier_20260911f/source.json) records toolbox, dependency and data provenance. Public/default sponsor data were used, with no outside substitute.

## Exact development results

Robust Sharpe is the minimum across 2016–2020 research and 2021–2022 development at 4%, 8% and 12% ATR-linked slippage. The complete zero/4/8/12 cost ladder, CAGR, Sortino, Calmar, hit rate, drawdown and turnover remain in the individual records. These are local historical measurements.

| Cell | Mode | Robust SR | Research SR, 12% | Dev SR, 12% | Worst DD, 12% |
|---|---|---:|---:|---:|---:|
| weekly_payoff_posterior_ablation | ablation | 0.970 | 1.621 | 0.970 | -23.3% |
| weekly_payoff_posterior_w84 | base | 0.944 | 1.445 | 0.944 | -38.1% |
| weekly_payoff_posterior_w126 | base | 0.788 | 1.500 | 0.788 | -37.9% |
| adaptive_expert_cash_falsifier | falsifier | 0.778 | 1.707 | 0.778 | -76.2% |
| adaptive_expert_cash_w84 | base | 0.671 | 1.472 | 0.671 | -82.2% |
| persistent_low_vol | control | 0.641 | 1.495 | 0.641 | -93.3% |
| adaptive_expert_cash_w126 | base | 0.571 | 1.572 | 0.571 | -79.0% |
| weekly_payoff_posterior_w168 | base | 0.538 | 1.153 | 0.538 | -38.3% |
| adaptive_expert_cash_w168 | base | 0.461 | 1.586 | 0.461 | -76.8% |
| adaptive_expert_cash_ablation | ablation | 0.444 | 1.463 | 0.444 | -77.4% |
| weekly_payoff_posterior_falsifier | falsifier | 0.409 | 1.290 | 0.409 | -40.3% |
| equal_liquid | control | 0.270 | 1.436 | 0.270 | -93.6% |
| triangle_coherence_ablation | ablation | 0.207 | 1.354 | 0.207 | -76.3% |
| inverse_vol_trend | control | 0.053 | 1.528 | 0.053 | -87.1% |
| triangle_coherence_falsifier | falsifier | -0.219 | 1.000 | -0.219 | -19.0% |
| triangle_coherence_w84 | base | -0.652 | 0.684 | -0.652 | -19.4% |
| triangle_coherence_w63 | base | -0.683 | 0.635 | -0.683 | -20.6% |
| triangle_coherence_w42 | base | -1.000 | 0.469 | -1.000 | -28.0% |

## Adjudication

**Weekly posterior:** the best base window (84 days) scored 0.944, with -38.1% worst stressed drawdown. The central 126-day model scored 0.788 versus 0.970 for its pooled-state ablation. Identity rotation reduced the central score to 0.409: asset-specific payoff history mattered in this implementation, but conditioning on the chosen binary market state did not earn its complexity. The central residual Sharpe against generic controls was 0.272. This is a useful decomposition, not a qualified alpha or permission to promote the pooled control.

**Signed triangles:** all three base windows had negative development Sharpe. The central score was -0.683 versus 0.207 for the level-only ablation and -0.219 for shuffled identities. The proposed improvement direction failed, despite the older unsigned-topology lead. Preserve their different source contexts; do not infer failure of every topology hypothesis.

**Adaptive policy:** the central score of 0.571 beat static equal thirds (0.444), but swapping trend and defensive utility labels was stronger (0.778). The best base was 0.671 and central stressed drawdown was -79.0%. Its 0.561 residual Sharpe does not rescue that failed policy interpretation. Strong correlation to the generic trend control (0.892) also reinforces the premeasurement classification as an allocator experiment.

No base window reached 1.0, and every central mechanism failed a defining control. The frozen rule therefore did not trigger the extra execution-day test or the already contaminated 2023–2024 diagnostic. No 2025+, live-window or account submission action occurred.

## Do the mechanisms change capital?

The following compares each matched central parent and control. Target differences cover all 2,922 input days including warm-up. Return differences use 2021–2022 net returns at 4% ATR costs and 2,000 circular 21-day block resamples with a predeclared seed. Intervals are annualized arithmetic percentage-point differences, not CAGR or multiple-testing-adjusted confidence.

| Parent | Control | Changed target days | Annualized return difference | 95% block interval |
|---|---|---:|---:|---|
| triangle_coherence_w63 | triangle_coherence_ablation | 97.0% | -29.45 pp | [-98.46, 39.69] pp |
| triangle_coherence_w63 | triangle_coherence_falsifier | 87.6% | -3.39 pp | [-10.45, 4.28] pp |
| weekly_payoff_posterior_w126 | weekly_payoff_posterior_ablation | 68.2% | -2.28 pp | [-8.75, 4.67] pp |
| weekly_payoff_posterior_w126 | weekly_payoff_posterior_falsifier | 63.7% | 7.85 pp | [-2.33, 20.85] pp |
| adaptive_expert_cash_w126 | adaptive_expert_cash_ablation | 93.2% | 13.61 pp | [-13.48, 42.62] pp |
| adaptive_expert_cash_w126 | adaptive_expert_cash_falsifier | 93.2% | -13.97 pp | [-26.60, -0.68] pp |

The mechanisms materially change target paths, so this campaign does not repeat Frontier-D's erased ordinal sizing interaction. Wide block intervals and the repeatedly inspected development sample limit inference. The repository freeze decisions are operational rules, not statistical proof that an economic idea can never work.

## Implementation and evidence health

- 41 new premeasurement tests passed: all modes and registered windows, prefix causality, 365-day replay, asset-order invariance, future-asset exclusion, graph arithmetic, fully realized weekly labels and delayed policy updates.
- All 18 measured objects completed exact evaluation and passed seven real-data prefix checkpoints. All three central portfolios were unchanged by the official cleaner; each candidate preserves its own cleaner diagnostics.
- 189 tests passed in the final repository run, including the captured source/data/registration linkage check; dashboard, compile and diff checks passed.
- Candidate packets retain exact parameters, registration/source/data/toolbox hashes, runtime, causality, cleaner changes and evidence stage. Policy packets explicitly retain `allocator_experiment`.
- Historical V10/V11/V12 matched streams and authenticated platform uniqueness remain PENDING; the generic-control regression is research-trained and evaluated on development.

## Next research boundary

Keep these formulas and parameter grids frozen. Do not turn the strongest control into a winner, invert triangle direction, or optimize policy temperatures after seeing these results. A subsequent campaign could preregister forecast calibration against a pooled probabilistic baseline, graph edge uncertainty rather than signed-balance change, or execution-aware policy utility rather than the current teacher proxy. Those are untested proposals and inherit no performance from this campaign.

## Reproduce

The dedicated `frontier-f-alpha-benchmark` workflow installs the frozen toolbox and core numerical dependency versions, runs the complete test suite, measures the campaign and attaches mechanism diagnostics. Preserve a new sponsor snapshot under its new data hash.

```bash
API_KEY=default python -m research.iteration \
  --manifest experiments/frontier_20260911f/manifest.json \
  --output results/frontier_20260911f --budget 18
python -m pytest -q tests
python scripts/build_research_dashboard.py --check
```
