# Breadth × dispersion completed-history adjudication — 2026-09-24

Status: **ADVANCE AS DIVERSIFIER; NOT PRISTINE OOS EVIDENCE**

Evidence semantics: `ADAPTIVE_REUSE`. The candidate predates this rolling evaluation, so these results must not be represented as untouched holdout/prequential selection evidence. Sponsor history ends 2026-09-23; the live boundary remains 2026-10-01.

Reproducibility anchor: GitHub Actions `q25-breadth-prequential` run 35961796159 on head `1fda291133d6016c0dae158efdf70e6612f22a05`; artifact `breadth-prequential-evidence` id 10793050382, SHA-256 `48d577c08bcb05f5fabfaa420264131affa895e4a02d0debaa15f491fad52053`. `research-integrity` run 35961796182 also passed on the same head.

## Frozen completed-history result

39 completed 90-day origins, 90-day step, minimum training history 730 days, 730-day recency half-life. Exact cost ladder: 4% / 8% / 12% ATR(14) per position-size change.

At 4% ATR, stitched candidate economics: annualized return 0.5802919689, annualized volatility 0.3735983278, Sharpe 1.5532509803, maximum drawdown -0.1976407605, and 10%-volatility-normalized return 0.1553250980. Positive-origin fraction is 0.5641025641. Mean origin Sharpe is 0.7049502798 unweighted and 0.4687546710 with the frozen recency weighting, showing material temporal instability despite positive aggregate economics.

Current-IS exact-cost sensitivity remains above the competition Sharpe gate across the frozen ladder: 4% ATR Sharpe 1.3386604832, CAGR 0.6928160458, max drawdown -0.5101992959, average turnover 0.0594423013; 8% ATR Sharpe 1.2079986148, CAGR 0.5897816671, max drawdown -0.5345200682, average turnover 0.0594814422; 12% ATR Sharpe 1.0763449665, CAGR 0.4928360618, max drawdown -0.5667137106, average turnover 0.0595210069.

## Incumbent comparison

VCB at 4% ATR has current-IS Sharpe 1.6482583590. Across the completed-origin stitched stream, VCB Sharpe is 1.4960392814 versus 1.5532509803 for breadth×dispersion. Candidate/VCB return correlation is 0.4716389493. The frozen 50/50 blend improves stitched Sharpe to 1.7574815000, annualized return 0.4369616028, annualized volatility 0.2486294182, maximum drawdown -0.0927146354, and 10%-volatility-normalized return 0.1757481500.

## Decision

Advance breadth×dispersion only as a diversification candidate. The exact-cost gate survives through 12% ATR and the frozen blend improves both Sharpe and drawdown versus either stitched component, which is useful evidence of complementarity. Do not promote it as a standalone production winner: the recency-weighted origin Sharpe of 0.4688 and 56.4% positive-origin rate expose meaningful regime dependence, and all historical backfill remains adaptive reuse.

No parameters were changed after observing these results.

## Next falsifiable experiment

Freeze and test a simple turnover-aware ensemble rule that combines VCB and breadth×dispersion without optimizing weights on these observed origins: equal-weight is the baseline; any proposed dynamic allocation must be preregistered from causal breadth/volatility state only, pass exact 4%/8%/12% ATR costs, prefix/replay and asset-order checks, and demonstrate improvement over the already-observed static 50/50 blend on genuinely forward evidence rather than by fitting this backfill.
