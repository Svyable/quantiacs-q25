# Frontier campaign B — topology, liquidity hysteresis, shock recovery

Campaign: `frontier_20260910b`

This campaign starts from clean `main` after the branch cleanup and deliberately avoids the already-implemented forecast-surprise, flow-absorption, and volatility-curve families.

## Research shape

The pre-return slate contains **24 hypotheses**:

- 8 residual correlation-topology ideas;
- 8 liquidity-transition / hysteresis ideas;
- 8 idiosyncratic shock-recovery ideas.

Six hypotheses were preregistered before performance inspection. Three were selected for implementation:

| Family | Core object | Nearest incumbent | Main destructive control |
|---|---|---|---|
| `topology_migration` | change in residual-network centrality during fragmentation | C165 / residual dispersion / V10 residual momentum | rotate node topology assignment |
| `liquidity_hysteresis` | recent re-entry × episode maturity × transition churn | V11 lifecycle | rotate episode metadata |
| `shock_recovery_surface` | shock depth × recovery slope × age × failed recovery | CoCrash126 / V10 residual momentum | rotate shock events across assets |

Three additional preregistrations remain intentionally unimplemented: topology-rank stability, first-entry vs re-entry, and recovery-breadth gating.

## Parameter discipline

Each implemented family has only two free parameters in the executable contract: `window` and `top_k`. `top_k` is fixed at 5 in this campaign; the only coarse grid is the named mechanism horizon.

No validation, 2025+, preview, or live data may drive candidate selection. The development engine ranks by the minimum Sharpe across research/dev and the 0.04/0.08/0.12 ATR cost rungs, with drawdown and turnover only as tie breakers.

## Run

```bash
python -m pytest -q tests
python -m research.iteration \
  --manifest experiments/frontier_20260910b/manifest.json \
  --output results/frontier_20260910b \
  --budget 18
```

No personal Quantiacs credential is required. The repo harness uses `API_KEY=default` for local/public market-data research.

## Evidence boundary

Before the benchmark workflow completes, every new strategy is `PENDING RESEARCH STRATEGY`. The frozen historical top-ten metrics do not attach to these files.

A development winner is not automatically promoted. Falsifier/ablation survival, validation, current full-IS eligibility, historical-core residual comparisons, multipass/runtime, and participant-specific uniqueness remain separate gates.
