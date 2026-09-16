# OMNI stock-turbulence IC-health overlay

Status: **PENDING market measurement**. Synthetic implementation checks passed before any return measurement; the local sandbox had no outbound network access, so real Quantiacs metrics must come from the dedicated GitHub Actions workflow.

## Classification

This is a **user-directed allocator experiment**, not an independent-alpha claim. The nearest incumbent is C165 / market-consensus risk timing. The changed novelty axes are:

1. **information primitive** — dynamic S&P 500 constituent state instead of crypto-only market state;
2. **timing/state condition** — the overlay abstains unless a fully realized online stock-to-crypto IC is healthy on both fast and slow windows.

Stock information can change only gross risk. Crypto identities and ranks are determined automatically from crypto data and contemporaneous `is_liquid`.

## Model

Five sponsor-data equity sensors are computed causally on dynamic S&P 500 constituents:

- 21/126-day realized-volatility term structure;
- covariance commonality, approximated as trailing equal-weight market variance divided by mean constituent variance;
- five-session downside breadth;
- 252-session drawdown pressure;
- cross-sectional dispersion relative to its trailing baseline.

Each scalar is mapped to `[0,1]` by a trailing 504-session median/IQR score. The component median is the turbulence state. Cross-sensor agreement is

`consensus = clip(1 - 2 * median(|component - turbulence|), 0, 1)`.

The stock state is carried to the crypto calendar, but IC samples are admitted only after a **fresh stock session**. At date `t`, the fast/slow IC correlates stock `risk_on[t-1]` with the crypto-market return already realized at `t`. There is no negative shift or future-return target.

For each IC window, reliability is Fisher transformed:

`z = atanh(IC) * sqrt(n - 3)`

and positive strength is `clip(z / 2, 0, 1)`. Health is the minimum of fast and slow strength, so either horizon can force abstention.

The gated gross multiplier is

`scale = exp(log(0.25) * health * consensus * turbulence)`.

Thus weak IC produces exactly `scale = 1`: the overlay does nothing. Full agreement, strong IC and extreme turbulence can reduce the parent to 25% gross.

## Parent and execution

The crypto parent is a compact automatic rank ensemble of residual momentum, path-efficient trend, low downside volatility and positive-return hit rate. It selects up to five positive-score liquid names and inverse-risk sizes them with a 25% name cap.

Name rotation and re-risk occur on Mondays or liquidity-universe changes. The turbulence layer may cut risk sooner only when desired gross is at least 15 percentage points below held gross. This is intended to preserve crash responsiveness without creating daily ATR-linked churn.

## Controls

- `base`: parent only;
- `ungated`: always trust turbulence (`health = 1`) — IC-health ablation;
- `inverted`: same health/consensus machinery but de-risk in calm states — directional falsifier;
- `gated`: preregistered candidate.

If the inverted control matches or beats the gated candidate, the claimed direction is falsified. If ungated matches or beats gated, the IC-abstention layer has not earned its complexity.

## Admissibility boundary

Quantiacs documents S&P 500 data via `qndata.stocks.load_spx_data` and documents multi-dataset backtests where one sponsor-provided dataset is used as an indicator for another traded dataset. Q25 rules require Sponsor-provided data only. However, generic platform availability is **not treated here as final Q25 clearance**; cross-dataset use remains `PROVISIONAL_HOSTED_PRECLEAR_REQUIRED` before submission.

References:

- https://quantiacs.com/documentation/en/data/stocks.html
- https://quantiacs.com/documentation/en/examples/q18_quick_start.html
- https://quantiacs.com/contest

## Reproduce

Synthetic integrity only:

```bash
python -m pytest -q tests/test_omni_stock_turbulence.py
```

Exact local/public data measurement:

```bash
API_KEY=default python strategies/generated/omni_stock_turbulence_ic_overlay.py \
  --research \
  --output results/omni_stock_turbulence_20260915/summary.json
```

Causal Quantiacs multipass candidate:

```bash
API_KEY=default python strategies/generated/omni_stock_turbulence_ic_overlay.py --multipass
```

Do not promote from the single-pass measurement alone. Hosted runtime, cleaner parity, Q25 cross-dataset admissibility and correlation/precheck remain separate gates.
