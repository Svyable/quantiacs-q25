# Frontier-O — price-volume absorption/release elasticity

Status: **IMPLEMENTED_PENDING_EVIDENCE**. This packet is frozen before Frontier-O market measurement.

## Thesis

A liquid asset can experience abnormal same-asset dollar-volume without producing much market-residual price displacement. Frontier-O treats that combination as **absorption**. The strategy only deploys after a stock of recent absorption is followed by positive residual displacement that is efficient relative to contemporaneous volume pressure.

This is deliberately different from V12-style cross-asset abnormal-volume diffusion and from generic downside-impact relief. The object is same-asset price displacement per abnormal dollar-volume pressure plus an explicit absorption-to-release state transition.

## Frozen cells

Base windows: **42 / 63 / 84**, central **63**. Top five names, Monday rebalance, 20% slots, unused gross in cash. Historical `is_liquid` is mandatory and liquidity loss exits immediately.

Ablation: remove dollar-volume pressure from the stored-absorption term while keeping displacement normalization, release confirmation and allocation unchanged.

Falsifier: rotate abnormal dollar-volume pressure among currently eligible assets each day before absorption is constructed. This preserves the cross-sectional pressure distribution while breaking the same-asset price-volume pairing.

The exact repository controls and ATR-linked cost ladder remain unchanged. Selection is restricted to research + dev; **2023-2024 is spent and excluded**. No post-measurement parameter rescue is allowed.

Preregistration SHA256: `51a2fede98155a65235f790baf1bb22b702dbe7a9d4a6de2cb119626863ce847`.
