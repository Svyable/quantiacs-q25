# AGENTS.md — Q25 Research Agent Entry Point

This is the first read for any coding/research agent in this repository.

The job is **not to produce more strategy files**. The job is to increase independent information about the Q25 portfolio: discover a causal mechanism, preregister it, implement it, dogfood the exact evaluator, try to destroy the thesis, and leave a traceable evidence packet.

## Read before touching strategy code

1. `configs/rules_snapshot.yaml`
2. `docs/LOCAL_RESEARCH_ACCESS.md`
3. `docs/EVIDENCE_MODEL.md`
4. `docs/RESEARCH_MATRIX.md`
5. `docs/AGENT_PROMPT.md`
6. `configs/historical_top10.yaml`
7. `configs/research_frontier.yaml`
8. `configs/external_research_leads.yaml`
9. `docs/EXTERNAL_RESEARCH_LEADS.md`
10. `docs/STRATEGY_ATLAS.md`
11. `docs/STRATEGY_GENERATION_PLAYBOOK.md`
12. `docs/RESEARCH_METHOD.md`
13. `docs/TESTING_PYRAMID.md`
14. `configs/promotion_gates.yaml`
15. `configs/chronological_folds.yaml`
16. `configs/cost_ladder.yaml`

Also inspect the executable incumbents and controls before claiming novelty. A new filename is not a new mechanism.

## The three-axis evidence model

Never collapse these into one status:

- **Strategy quality** — economics of a valid observed return stream: robust Sharpe, CAGR/return, Sortino, Calmar, drawdown, turnover, cost sensitivity, residual contribution.
- **Evidence quality** — development vs validation vs diagnostic vs authenticated preclear, provenance hashes, completeness, comparable harness.
- **Implementation health** — source audit, causality, liquid-only, long-only, cleaner parity, bounded replay, runtime.

A software/integrity failure is **not** a zero Sharpe and does not automatically falsify every other preregistered cell in the family. A great development Sharpe is also **not validation**.

`docs/EVIDENCE_MODEL.md` is normative.

## Local Quantiacs access — do not block on credentials

A personal Quantiacs API key is not required for local/public-data research. The repo configures **`API_KEY=default` before importing `qnt`** when no participant credential is present.

Therefore:

- do not ask the user for credentials before local research;
- do not mark performance `PENDING` just because a personal key is absent;
- run exact Quantiacs local stats when the public/default endpoint is reachable;
- reserve authenticated credentials for participant-specific correlation/precheck, identity and submission;
- if public infrastructure fails, record `BLOCKED_INFRA`, preserve the frozen candidate, and do not retune while fixing infrastructure.

See `docs/LOCAL_RESEARCH_ACCESS.md`.

## Dogfood contract

A strategy change is incomplete until the same repository machinery used to criticize incumbents has criticized it.

Default loop:

```text
map nearest incumbent
→ generate broad hypothesis slate
→ score novelty/falsifiability before returns
→ preregister
→ causal implementation
→ static/unit/prefix/replay checks
→ API_KEY=default exact Quantiacs run
→ candidate packet
→ ablation + destructive falsifier
→ residual/control diagnostics
→ evidence-aware matrix
→ kill / repair / forward-test
```

Each attempted cell must emit or preserve:

- campaign / candidate / family / mode / exact params;
- preregistration, source, data and toolbox hashes;
- evidence stage and Quantiacs access mode;
- failure status **and failure stage** if invalid;
- Sharpe across research/dev × configured cost ladder;
- worst-fold/cost Sharpe;
- CAGR, Sortino, Calmar and hit-rate where return streams support them;
- max drawdown and turnover;
- causality / prefix / bounded replay status;
- cleaner parity;
- destructive-control relationship;
- available residual/correlation diagnostics.

Missing evidence stays missing. Never copy a metric from a related implementation.

After changing canonical evidence, run:

```bash
python scripts/build_research_dashboard.py
python scripts/build_research_dashboard.py --check
python -m pytest -q tests
```

The generated `docs/RESEARCH_MATRIX.md` and `docs/data/strategy_matrix.json` are public views, not hand-edited scoreboards.

## Current read-through

Frontier-G (`experiments/frontier_20260911g/pm_report.md`) tested residual-edge
uncertainty change, two-speed forecast agreement and cost-relative residual
persistence. All 18 objects completed exact local evaluation after a
coordinate-order repair in the agreement family. Agreement was frozen as
`KILL_WEAK_ALPHA`: the central 42-day base scored 0.458, beat both its ablation
(0.255) and disagreement falsifier (−0.134), and still missed the 1.0 floor.
Edge-uncertainty change and cost-relative persistence were frozen as
`FALSIFIED_DEVELOPMENT`. Preserve these formulas and grids. No execution-delay
or later chronological diagnostic was triggered. Full evidence is in
`evidence/frontier_20260911g/` with source and preregistration freezes.

Frontier-F (`experiments/frontier_20260911f/pm_report.md`) tested signed-triangle
coherence, a conditional weekly-payoff posterior and an adaptive expert/cash
policy. The policy is an `allocator_experiment`, not independent alpha. All 18
objects completed exact local evaluation; all three approaches were frozen as
`FALSIFIED_DEVELOPMENT`. The best base posterior scored 0.944; its central
market-state-conditioned model lost to the pooled-state ablation. The policy
lost to swapped expert labels, and every signed-triangle base had negative
development Sharpe. Preserve these formulas and grids. No execution-delay or
later chronological diagnostic was triggered. Full evidence is in
`evidence/frontier_20260911f/` with source and preregistration freezes.

Frontier-E (`experiments/frontier_20260911e/pm_report.md`) tested downside impact
relief, range acceptance escape and upside response convexity. All 18 objects
completed exact local evaluation, but all three families were frozen as
`FALSIFIED_DEVELOPMENT`. Convexity's best base robust Sharpe was 0.827; its
inverted control was stronger at 0.985. Neither is a promotion. Unlike the
Frontier-D ordinal interaction, these defining transforms do materially alter
capital. Preserve their failed directions and grids; do not rescue them by
retuning. No later chronological window was opened. See the separate
`evidence/frontier_20260911e/` context and immutable implementation freeze.

Frontier-D (`experiments/frontier_20260910d/pm_report.md`) measured all ten
candidate cells and three controls with exact public/default Quantiacs data.
Both variance-ratio reversal and rank-transition reliability were frozen as
`FALSIFIED_DEVELOPMENT`; do not rescue them with a wider parameter grid. The
rank-reliability term produced identical development returns to its ablation.
Use `research/mechanism_diagnostics.py` to check whether proposed signal changes
survive portfolio construction, and preserve eligibility exits until the next
scheduled rebalance. Evidence is in `evidence/frontier_20260910d/` and remains
separate from older campaign contexts.

The latest observed Frontier-B packet is **development only**. Its strongest valid base cell is `topology_migration_w84`; topology is therefore a priority seam for forward research, not a production winner. One topology grid cell failed implementation/integrity and must be repaired without parameter expansion.

The liquidity-hysteresis base family is weak as standalone alpha in the captured development packet. Preserve lifecycle/hysteresis as a possible conditioning variable; do not keep tuning the same standalone hypothesis.

Shock-recovery base economics remain unresolved because invalid implementation cells did not earn a valid return stream.

The historical V10/V11/C165/V12/defensive roster remains a **separate frozen evidence lane** until those exact implementations are brought through the current harness.

## Family adjudication

Independent preregistered cells should continue running even when a sibling cell fails.

Use:

- `CONTINUE / NEEDS_FORWARD_EVIDENCE` when valid development evidence survives controls;
- `CONTINUE / REPAIR_INVALID_CELLS_THEN_FORWARD` when promising valid cells coexist with implementation/integrity failures;
- `FREEZE / KILL_WEAK_ALPHA` when every valid base cell is below the predefined development floor;
- `FREEZE / FALSIFIED_DEVELOPMENT` when a valid destructive control or ablation matches/beats its valid parent;
- `PENDING / INSUFFICIENT_VALID_EVIDENCE` when no valid base cell exists.

Do not family-rank a campaign with unattempted preregistered cells.

## Novelty gate before returns

For an independent alpha, compare with the nearest incumbent on:

1. information primitive;
2. transform;
3. timing/state condition;
4. portfolio construction.

Require at least **two changed axes** before calling it a new alpha family. A new lookback, threshold, top-K, cap, classifier, smoothing constant or blend weight is usually a refinement.

The default campaign remains **24 hypotheses → 6 preregistrations → at most 3 implementations**.

## Frontier pressure

Do not let a successful family create a monoculture. Current useful seams include correlation-topology change, topology rank stability, fragmentation/recovery, volatility term structure, forecast surprise/disagreement, price-volume elasticity, assimilation-delay dynamics, tail dependence, range-volume geometry, opportunity density, and execution-aware alpha density.

On-chain state and index ecology remain `UNVERIFIED_FOR_Q25` until current admissibility, timestamps, replay and runtime are established. `configs/external_research_leads.yaml` and `docs/EXTERNAL_RESEARCH_LEADS.md` contain provenance and caveats.

For any **forecast surprise** or ML idea, start with a tiny causal model and a non-ML ablation. For **price-volume elasticity**, destroy the price/volume pairing as a mechanism falsifier rather than merely shifting a lookback.

## Falsification beats tuning

Use destructive controls that attack the proposed causal story:

- remove the defining transform;
- permute identities/dates while preserving marginal distributions;
- replace the state with a matched generic market state;
- freeze online coefficients;
- add execution delay;
- invert the gate;
- replace exact ecology/lifecycle information with simple `is_liquid`.

If the destructive control preserves the edge, the story is wrong or incomplete.

Do not rescue a failed family by widening the parameter grid after seeing returns.

## Hard prohibitions

- no fabricated or transplanted metrics;
- no future leakage, centered windows or negative shifts;
- no manual symbols;
- no external non-Quantiacs strategy data in contest code;
- no full-history Sharpe hyperparameter optimizer as evidence;
- no one-point optimum promotion;
- no blend-weight rescue after a failed correlation gate;
- no fitting on the 2026-10-01 → 2027-01-31 live window;
- no treating leaderboard titles as implementation disclosure;
- no treating a software exception as economic falsification;
- no stopping local research to request a personal key before trying `API_KEY=default`.

A successful agent run may promote **zero** strategies. Success is a cleaner frontier, stronger controls, repaired measurement, and more information per research look.
