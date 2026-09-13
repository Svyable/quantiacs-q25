# Frontier-L PM report — observed development evidence

Frontier-L is now observed development evidence. The frozen preregistration was measured unchanged with the repository's exact public/default Quantiacs harness on the reused 2016–2022 development surface. All **18** cells completed: 15 preregistered family/base/control cells plus the three generic benchmark controls. The already-spent 2023–2024 validation fold was excluded.

| Family | Best base robust SR | Central robust SR | Ablation | Falsifier | Decision |
|---|---:|---:|---:|---:|---|
| `dollar_volume_share_migration` | **0.614** (`w42`) | 0.614 | 0.281 | -0.201 | `KILL_WEAK_ALPHA` |
| `permutation_entropy_contraction` | **0.401** (`w126`) | -0.046 (`w84`) | 0.166 | 0.132 | `FALSIFIED_DEVELOPMENT` |
| `relative_value_convergence` | **0.182** (`w63`) | -0.024 (`w42`) | -0.015 | -0.471 | `FALSIFIED_DEVELOPMENT` |

## Read-through

Dollar-volume share migration is the only Frontier-L family whose central parent beats both matched destructive controls. That is useful causal support, but **not sufficient economics**: every preregistered base window remains below the fixed robust-development Sharpe floor of 1.0. Freeze it as `KILL_WEAK_ALPHA`; do not widen the grid.

Permutation-entropy contraction is falsified at the preregistered central cell: both the entropy-level ablation and identity-rotation falsifier beat the central contraction signal. Relative-value convergence is also falsified: the unconditional laggard ablation slightly beats the dispersion-contraction parent. Do not invert either observed direction or parameter-rescue after seeing returns.

**Promotion: zero.** No Frontier-L family earns forward evidence. `topology_migration_w84` remains a failed former development leader because its frozen 2023–2024 forward gate already produced 0.314 Sharpe at 12% ATR-linked cost.

## Provenance

- GitHub Actions workflow run: `34733083803`
- Artifact: `10309964229` (`frontier_20260912l-measured-34733083803`)
- Artifact digest: `sha256:87396b2d8ba174df29f05806ceb5221e3457672d44a45f7253720028003e1298`
- Measured head: `f1f236cdb83222be74be19c6244b2ac546781710`
- Quantiacs access: `public_default`
- Data SHA256: `bc932fc6f016c2bc0fbf3f51bf6f59b48d895cd1ac7ed27602d63ecbfdc8bc58`

The repository preserves the exact observed summary, context, residual diagnostics and an immutable copy of the measured matrix. Raw per-day return streams remain anchored in the immutable Actions artifact rather than being duplicated into Git history.

## Next boundary

Do not retune Frontier-L. Preserve dollar-volume share migration as a causally supported but economically weak result, and preserve the two falsified directions. Keep 2023–2024 closed. The next useful research action is a genuinely new object or bringing the frozen historical V10/C165/V12 implementations through the current harness for comparable controls.
