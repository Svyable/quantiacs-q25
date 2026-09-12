# Topology migration — observed 2023–2024 forward validation

> **Fold status: SPENT.** This was the first chronological 2023–2024 look for the already-selected Frontier-B topology-migration family. The run was preregistered on PR #22 before the returns were opened. No parameter changes are permitted from this result, and this fold must never again be described as untouched or used to mutate strategy formulas.

**Observed decision: `FAIL_FORWARD_GATE`**

| Object | Type | Validation SR @0% | SR @4% | SR @8% | SR @12% | CAGR @12% | Max DD @12% | Turnover @12% |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `topology_migration_w42` | base | 1.049 | 0.899 | 0.748 | 0.596 | 0.121 | -0.308 | 0.049 |
| `topology_migration_w63` | base | 0.358 | 0.194 | 0.031 | -0.132 | -0.051 | -0.356 | 0.045 |
| `topology_migration_w84` | base | 0.813 | 0.647 | 0.481 | 0.314 | 0.044 | -0.251 | 0.042 |
| `topology_migration_ablation` | ablation | -0.053 | -0.218 | -0.382 | -0.544 | -0.197 | -0.502 | 0.071 |
| `topology_migration_falsifier` | falsifier | 0.151 | -0.006 | -0.163 | -0.318 | -0.091 | -0.379 | 0.043 |
| `equal_liquid` | control | 1.528 | 1.493 | 1.459 | 1.425 | 0.872 | -0.384 | 0.039 |
| `inverse_vol_trend` | control | 1.345 | 1.110 | 0.875 | 0.640 | 0.208 | -0.507 | 0.154 |
| `persistent_low_vol` | control | 1.900 | 1.862 | 1.823 | 1.784 | 1.145 | -0.330 | 0.042 |

## Predeclared gate from the executed PR #22 protocol

- **FAIL** — selected `w84` SR@12 = **0.314**, required >= 1.000.
- **PASS** — selected `w84` remained positive at every frozen cost rung.
- **PASS** — canonical `w63` still beat the original ablation and falsifier at 12% ATR: -0.132 vs -0.544 / -0.318.
- **PASS** — two of three base windows remained positive at 12% ATR.

The family therefore retains evidence that the migration transform is economically distinct from its destructive controls, but the selected development winner did **not** transport strongly enough to the forward period. `topology_migration_w84` is not a validated production candidate in this formulation.

## Validation-only correlation diagnostic at 4% ATR cost

`topology_migration_w84` versus generic controls:

- `equal_liquid`: 0.483
- `inverse_vol_trend`: 0.485
- `persistent_low_vol`: 0.424

## Provenance

- workflow run: `34675541608`
- artifact id: `10292266847`
- artifact name: `topology-forward-validation-34675541608`
- artifact SHA-256 digest: `ffa6d27cab060afd77e1cd9a67715e504cf73bbcfb99d35e733ac1344e1db44f`
- executed PR: `#22` (`codex/topology-forward-validation`)
- executed head SHA: `1675aee27d67ed5e98b4e78c2cdc00f79c8280a7`
- validation dates: 2023-01-01 through 2024-12-31
- access mode: `public_default`
- data SHA-256: `13c7525e7eaf3ffec5df639adb3f17aef243469330724ae4a326e1a72954dc60`
- strategy SHA-256: `f93f33a2c6eceec14e7555fb8a864f50d49eebe7b33a870282e3564ec3c0073d`
- original Frontier-B preregistration SHA-256: `bd61d69cd3859ee459162755259281e1fc9b741e8a4a6e2624e49c98a4b660d4`
- executed PR #22 validation-plan SHA-256: `1f878a84eb42564635e225a02740837aad220c2fae237bbe671ee2ddb6c5147e`

The executed PR #22 protocol and the later report-only validation contract merged by PR #26 are different administrative artifacts. The market window was already observed by #22 before #26 merged, so the later plan cannot restore pristine status.

## Research consequence

Do **not**:

- switch from w84 to w42 because w42 happened to validate better;
- relax the 1.0 gate after observing 0.314;
- tune graph lag, lookback, trend gate, position count, or caps on 2023–2024;
- use 2025+ to repair this strategy;
- describe 2023–2024 as an untouched validation fold again.

New alpha research may continue on the already-reused 2016–2022 development surface with fresh preregistrations, but this forward window is permanently diagnostic-only for any newly invented family.

These are historical simulations, not forecasts or guarantees.
