# Frontier-N — online AR surprise persistence

Status: **measured; FALSIFIED_DEVELOPMENT; frozen; promote zero**.

This campaign tests one priority-1 frontier from `configs/research_frontier.yaml`: whether the realized error of a deliberately tiny causal forecast contains cross-sectional information beyond ordinary residual momentum.

Review classification: **family refinement**. The earlier [Frontier-A forecast-surprise implementation](../../strategies/generated/frontier_20260910_forecast_surprise.py) already uses lagged rolling AR(1) errors of market-residual returns. Frontier-N adds prior-error scaling, coefficient clipping and a positive-surprise persistence gate. These changes do not establish an independent alpha family. The original `novel_alpha` preregistration remains unchanged as a historical record.

The canonical candidate estimates a rolling per-asset AR(1) model of equal-weight-market residual returns using training pairs ending at `t-1`. It standardizes the current innovation by prior forecast-error volatility, requires at least three positive surprises across the last five completed bars, and allocates to the five strongest positive persistence scores on Mondays. The raw-residual ablation keeps every portfolio rule fixed while removing the forecast object. The falsifier rotates surprise identities across eligible assets each date.

No Frontier-N return evidence was observed before the preregistration hash `a29d5e42055f5af420178bf6dd924453a48561bf25c349cfd68662b962d0b062` was frozen. The exact repository benchmark owns economic adjudication; no parameter rescue is permitted after measurement.

The first successful [measurement run](https://github.com/Svyable/quantiacs-q25/actions/runs/34739055893) completed all five preregistered cells and three baselines on the reused 2016–2022 development surface. The score is the minimum research/dev Sharpe across 4%, 8% and 12% ATR-linked costs.

| Cell | Robust development Sharpe |
|---|---:|
| Base, 63-day fit | -0.676254 |
| Central base, 84-day fit | -0.780484 |
| Base, 126-day fit | -1.305558 |
| Raw-residual ablation | -1.001414 |
| Identity-rotation falsifier | -0.519881 |

The identity-rotation falsifier beat the central parent. The ablation did not. Every base missed the fixed 1.0 floor. These results freeze the family; they do not justify inversion, parameter rescue or promotion.

The [measurement receipt](../../evidence/measurement_receipts/frontier_20260912n.json) preserves the first run's source, data, manifest, toolbox and artifact provenance. Canonical packet ingestion remains pending; the receipt is separate from canonical ranking evidence. The strategy's docstring and hashed preregistration retain their premeasurement wording because those measured source bytes remain frozen.
