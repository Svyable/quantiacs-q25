# Reproducibility Health

> Replay consistency is an evidence-quality channel. It is not a strategy-performance score.

Campaign: **`frontier_20260912k`**  
Status: **`DECISION_STABLE_CONTEXT_DRIFT`**

## Replay pulse

| Check | State |
|---|---|
| Family decisions stable | **3/3** |
| Best-base + central identity stable | **3/3** |
| Max absolute summary-metric delta | **6.156e-09** |
| Manifest hash match | **yes** |
| Strategy source hashes match | **yes** |
| Data hash match | **no** |
| Benchmark source hash match | **no** |
| Fold / cost policy match | **yes** |

## Contexts

- Local canonical packet: Python `3.13.9`, data `8bf943c40074d4107cb63edda99a7b0b268ac8ed0080fcf6de04d871ad21cd09`, benchmark `8fbe3f5e463a97f5e0fe697e044a35d3fb49e234c69e1d1d0d05e75f3b40c825`.
- CI replay: Python `3.11.16`, data `bc932fc6f016c2bc0fbf3f51bf6f59b48d895cd1ac7ed27602d63ecbfdc8bc58`, benchmark `93e0abcdcc90620bd9b8f7080900ebc1a50e1ec9f1380cb8cbfc2262c474e4f2`; workflow `34716313017`, artifact `10304184100`.

The strategy files and frozen manifest are the same, while the data snapshot and benchmark source context differ. The family decisions remain stable and the observed summary-metric drift is tiny, but the two packets are **not byte-identical reproductions**. Their metrics must remain in separate provenance contexts.

## Family replay comparison

| Family | Decision | Best base | Central | Max metric Δ |
|---|---|---|---|---:|
| `cohort_residual_divergence` | MATCH | MATCH | MATCH | 4.317e-09 |
| `nearest_peer_detachment` | MATCH | MATCH | MATCH | 5.136e-09 |
| `subspace_rotation_opportunity` | MATCH | MATCH | MATCH | 6.156e-09 |

## Recursive rule

A replay may confirm a decision without becoming the same evidence packet. Data hash, evaluator hash, source hashes, fold policy, and access mode are evidence-quality dimensions. **Never average, splice, or silently replace metrics across non-identical contexts.** If a replay changes a family decision or selected identity, treat that as decision drift and fail CI until reconciled.
