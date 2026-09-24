# Frozen preregistration: turnover-aware VCB × breadth-dispersion ensemble

Status: **FROZEN BEFORE ECONOMIC EVALUATION**
Date: 2026-09-24
Base commit: `fa661c06649e5717fcdd0b5f05074a288fb36c7e`

## Hypothesis

Breadth-dispersion is sufficiently independent of VCB to improve portfolio economics, but the observed static 50/50 blend is a high-turnover upper baseline. A causal no-trade-band allocator can preserve most diversification benefit while reducing position-size changes under the official ATR transaction-cost model.

## Frozen mechanism

Use only the already-permitted Quantiacs Sponsor `crypto_daily_long` data and the automatic top-10 monthly liquid universe. Generate VCB and breadth-dispersion weights with their already-frozen rules. The portfolio target is the static 50/50 asset-weight blend. Apply an asset-level no-trade band: retain the previous implemented asset weight when the absolute target-weight change is < 0.02; otherwise move to the current target. After the band, clip negative weights to zero and rescale only when gross long exposure exceeds 1.0. No asset names, dates, year switches, or hand selection are allowed.

The 0.02 threshold is frozen here and will not be tuned after observing economic results. It is chosen as a simple two-percentage-point implementation threshold, not from a grid search.

## Baselines and destructive control

Compare against: (1) VCB alone; (2) breadth-dispersion alone; (3) the already-observed static 50/50 blend with no band. Destructive control: one-day-lag the *allocator target* an additional day beyond the normal causal strategy timing while keeping all other mechanics identical. This should not improve the claimed execution edge systematically; if it does, interpretation is weakened.

## Required integrity checks

Long-only; gross exposure <= 1; monthly-liquid-universe compliance; asset-order invariance; prefix invariance; bounded replay; deterministic rerun tolerance; no future-data access; same rule over the full evaluation period. Where supported by the strategy interface, require single-pass/multipass parity.

## Frozen evaluation

Use completed Sponsor history only and do not cross the 2026-10-01 live boundary. Historical evidence is `ADAPTIVE_REUSE`, not pristine OOS evidence. Evaluate exact 4%, 8%, and 12% × ATR(14) transaction costs. Report annualized return, volatility, Sharpe, maximum drawdown, turnover/position-change reduction, 10%-vol-normalized return, correlation to each component, regime/origin stability, positive-origin fraction, and recency-weighted origin Sharpe. Preserve exact date bounds and deterministic evidence hashes.

## Advancement gates

The turnover-aware ensemble advances only if all integrity checks pass and, at official 4% ATR cost: (a) current-IS Sharpe since 2016-01-01 remains > 1.0; (b) position-change turnover is at least 10% lower than the static 50/50 blend; (c) Sharpe is no worse than 0.10 below the static blend's already-observed 1.75748; (d) 10%-vol-normalized return is no worse than 1.0 percentage point below the static blend's already-observed 17.57%; and (e) max drawdown is not worse by more than 3 percentage points versus the static blend's already-observed -9.27%. It must also remain >1.0 Sharpe at 12% ATR cost to demonstrate cost robustness.

Failure is preserved as a falsification; no post-result threshold grid or rescue tuning is permitted.