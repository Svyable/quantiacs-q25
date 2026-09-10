# Frontier campaign — 2026-09-10

Decision: **reserve as unvalidated research; zero strategies promoted.**

Three new mechanism hypotheses were implemented, with three preregistered
reserves. The 24-hypothesis slate spans forecast errors, price-volume geometry,
volatility structure, and membership/topology. It was scored before any returns.

## Observed evidence

- 27 software tests passed locally: deterministic weights, asset-order invariance,
  missing prices/volume/membership, all-cash intervals, single-asset capacity,
  weekly timing, prefix invariance, bounded replay, future perturbations, cost
  adapter contracts, ranking eligibility, falsifier freezes, and budget/resume.
- Python compilation and the existing static-audit self-test passed.
- Real benchmark command was attempted and returned exit code 2: `API_KEY` was
  missing. No market data were downloaded and no economic metrics were computed.
- All candidate and family performance ranks are PENDING. No in-sample Sharpe,
  return, drawdown, cost resilience or correlation result is claimed.

The immutable blocked attempt is included under `benchmark_attempt/`.
The exact software test report is in `software_validation.json`.

## Evidence ladder

| Level | Status | Evidence or missing requirement |
|---|---|---|
| L0 | PASS locally | Long-only, finite weights, historical liquidity, cap/gross tests; source review |
| L1 | PASS on synthetic panels | Determinism, timing, cash and adverse input tests |
| L2 | PASS on synthetic panels | Prefix, future perturbation and finite replay; real-data/platform parity pending |
| L3 | PENDING | Exact Quantiacs market-data stats need API key and toolbox |
| L4 | PENDING | Four ATR rungs wired and contract-tested, no economic results |
| L5 | PENDING | Real regime evidence not run |
| L6 | PARTIAL engineering only | Research/dev selection enforced; validation remains untouched |
| L7 | PENDING | Development-fitted control residual adapter implemented; actual streams absent |
| L8 | PASS registration | Six hashed preregistrations, finite grid, attempts and formula ledgers |
| L9 | PENDING economically | Falsifier/ablation implementations tested; no market results |

These software checks do not constitute official contest admissibility or proof
of no bias. Complete replay and sponsor checks are still required.

## Registration and source revision

Each family has its own `preregistration.json` and SHA256. The originally hashed
render template is preserved as `preregistered_template.py.txt`. Before market
performance was observed, software tests found that pandas sorted columns after
cross-asset permutation in the two destructive controls. The implementation and
active template now restore the original asset-coordinate order. This is a
mechanical bug fix, not a hypothesis change; original preregistrations are retained.
Final executable code hashes accompany each future run's context.

## Falsifiers, costs and originality

Forecast surprise must beat raw residual returns and wrong-asset forecasts.
Flow absorption must beat flow alone and destroyed price/flow pairing. The
volatility-curve family must beat inverse long volatility and an inverted curve
state. A canonical control matching/beating its parent freezes the family.
The three coarse lookbacks measure a plateau; only the canonical setting has
matched destructive controls in this campaign. Do not promote a grid winner as
an independent validated mechanism.

The research engine compares equal-liquid, inverse-vol trend, and persistent
low volatility on identical folds/costs. Historical roster values are preserved,
never mixed into the new ranking. V10/V11/V12 matched return streams and current
hosted uniqueness evidence are still required for an independence claim.

## Multiple-testing and next frontier

There have been **zero market-performance looks** in this campaign. The declared
budget is 18 weight paths, each with two folds and four costs (144 exact stats
calls if the entire campaign succeeds). Reruns preserve failed evaluations; new
code/data identities count as further research looks rather than fresh holdouts.

Next: configure the Quantiacs API key privately and run the declared campaign.
Follow the falsifier freeze decisions before allocating further research effort.
No mechanism frontier has been empirically narrowed yet. The remaining three
registered ideas—model disagreement, membership re-entry hysteresis, and bridge
migration—are reserves, not an automatic response to a disappointing Sharpe.

Existing unset policy thresholds, full-IS eligibility, validation/diagnostic
analysis and hosted checks remain explicit. No contest submission was made.
