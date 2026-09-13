# Frontier-N — online AR surprise persistence

Status: **implemented, preregistered, unmeasured**.

This campaign tests one priority-1 frontier from `configs/research_frontier.yaml`: whether the realized error of a deliberately tiny causal forecast contains cross-sectional information beyond ordinary residual momentum.

The canonical candidate estimates a rolling per-asset AR(1) model of equal-weight-market residual returns using training pairs ending at `t-1`. It standardizes the current innovation by prior forecast-error volatility, requires at least three positive surprises across the last five completed bars, and allocates to the five strongest positive persistence scores on Mondays. The raw-residual ablation keeps every portfolio rule fixed while removing the forecast object. The falsifier rotates surprise identities across eligible assets each date.

No Frontier-N return evidence was observed before the preregistration hash `a29d5e42055f5af420178bf6dd924453a48561bf25c349cfd68662b962d0b062` was frozen. The exact repository benchmark owns economic adjudication; no parameter rescue is permitted after measurement.
