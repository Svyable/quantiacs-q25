# Frontier campaign G — edge uncertainty, forecast agreement, cost-relative persistence

Campaign: `frontier_20260911g`

This campaign starts after Frontier-F froze signed-triangle change, conditional weekly posteriors, and adaptive expert routing. It does not reuse those formulas or grids.

## Research shape

The pre-return slate contains **24 hypotheses** across four areas:

- residual-graph uncertainty;
- two-speed / calibration forecast structure;
- execution-aware density;
- opportunity-state cash gates.

Six hypotheses were preregistered before performance inspection. Three were selected for implementation:

| Family | Core object | Nearest incumbent | Main destructive control |
|---|---|---|---|
| `edge_uncertainty` | change in residual-edge correlation variance | Frontier-B topology migration / Frontier-F signed triangles | rotate uncertainty-change |
| `forecast_agreement` | rank agreement of slow and 7-day residual forecasts | Frontier-A AR surprise / Frontier-F weekly posterior | score disagreement instead |
| `cost_relative_persistence` | persistent residual edge / own relative ATR | V10 residual momentum / unimplemented execution hurdle | rotate ATR identities |

Three additional preregistrations remain intentionally unimplemented: spectral-gap change, leader-response lag, and residual rank-stability density.

## Parameter discipline

Each implemented family has only two free parameters in the executable contract: `window` and `top_k`. `top_k` is fixed at 5; the only coarse grid is the named mechanism horizon.

No validation, 2025+, preview, or live data may drive candidate selection. The development engine ranks by the minimum Sharpe across research/dev and the 0.04/0.08/0.12 ATR cost rungs, with drawdown and turnover only as tie breakers.

## Run

```bash
python -m pytest -q tests
python -m research.iteration \
  --manifest experiments/frontier_20260911g/manifest.json \
  --output results/frontier_20260911g \
  --budget 18
```

No personal Quantiacs credential is required. The repo harness uses `API_KEY=default` for local/public market-data research.

## Evidence boundary

Measured development results live in [`evidence/frontier_20260911g`](../evidence/frontier_20260911g) and the [PM report](../experiments/frontier_20260911g/pm_report.md). All three families were frozen. A development score is not contest qualification.
