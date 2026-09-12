# Frontier campaign H — clustering escape, factor-loading escape, neighbor identity

Campaign: `frontier_20260911h`

This campaign starts from `main` after Frontier-F and does **not** retune any A–F formula. The only new-campaign family that cleared the internal development floor is Frontier-B `topology_migration` (unsigned residual-correlation centrality change during fragmentation). Frontier-H tests three different objects on that seam.

## Research shape

The pre-return slate contains **24 hypotheses** across:

- local graph structure (clustering, k-core, triangle counts);
- spectral / factor topology (leading loadings, gap, subspace drift);
- neighbor-identity dynamics (set churn, rank inversion, delayed neighbor beta);
- residual opportunity geometry (rank-stability breadth, failed recovery, path/range wedge).

Six hypotheses were preregistered before performance inspection. Three were selected for implementation:

| Family | Core object | Nearest incumbent | Main destructive control |
|---|---|---|---|
| `clustering_escape` | falling Onnela weighted clustering of \|residual corr\| during mean-\|corr\| fragmentation | topology_migration degree-centrality change | rotate clustering-change |
| `factor_loading_escape` | falling absolute loading on the leading residual-corr eigenvector during spectral-gap compression | topology_migration / C165 | rotate loading-change |
| `neighbor_identity_churn` | Jaccard turnover of each name's top residual neighbors | topology_migration / static low-correlation | rotate churn scores |

Three additional preregistrations remain unimplemented: spectral-gap cash gating, bridge betweenness, and failed-recovery count.

## Parameter discipline

Each implemented family has only two free parameters in the executable contract: `window` and `top_k`. `top_k` is fixed at 5; the only coarse grid is 42/63/84.

No validation, 2025+, preview, or live data may drive candidate selection. The development engine ranks by the minimum Sharpe across research/dev and the 0.04/0.08/0.12 ATR cost rungs.

## Run

```bash
python -m pytest -q tests
python -m research.iteration \
  --manifest experiments/frontier_20260911h/manifest.json \
  --output results/frontier_20260911h \
  --budget 18
```

No personal Quantiacs credential is required. The repo harness uses `API_KEY=default` for local/public market-data research.

## Evidence boundary

Before the benchmark completes, every new strategy is `PENDING RESEARCH STRATEGY`. The frozen historical top-ten metrics do not attach to these files. A development winner is not automatically promoted.
