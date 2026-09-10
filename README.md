# quantiacs-q25 — Q25 Quantitative Research Lab

> 🌐 **Q25 Quant Lab site:** https://svyable.github.io/quantiacs-q25/
>
> The Pages site is the public-facing research surface: the historical Top-10 roster, mechanism atlas, research/testing system, evidence boundaries, and selected frontier work in a form that is easier to browse than the raw repo. **The repository remains the source of truth.** If the URL has not been activated yet, enable **Settings → Pages → Source: GitHub Actions**; `.github/workflows/pages.yml` will build and deploy `docs/` automatically from `main`.

## Executable frontier campaign

Three new standalone families—forecast surprise, flow absorption, and volatility
curve shape—have a 24-hypothesis slate, six preregistrations and an exact
Quantiacs benchmark/iteration engine.

```bash
python -m pytest -q tests
python -m research.iteration --budget 18
```

**No personal Quantiacs API key is required for local research.** When `API_KEY`
is absent or blank, the repo harness injects `API_KEY=default` before importing
`qnt`. That behavior is supported by the current open-source Quantiacs toolbox,
which explicitly special-cases `default` and uses it in its own tests.

A real participant credential is reserved for **account-bound** operations such as
participant-specific remote correlation/precheck, account identity and submission.
Local/public market-data backtests and local Quantiacs stats should be measured
without waiting for one. See [Local Research Access](docs/LOCAL_RESEARCH_ACCESS.md).

The checked-in blocked benchmark attempt predates this fix. It is retained as audit
history, not as evidence that public Quantiacs data require a personal key. Rerun
the same frozen campaign with the corrected harness before changing its parameters.

See [engine usage and evidence boundaries](docs/FRONTIER_ITERATION.md) and the
[campaign report](experiments/frontier_20260910/pm_report.md).

**Causal crypto alpha. Orthogonality before cosmetics. Costs before screenshots. Live-window robustness over backtest theater.**

This repository is our research-and-validation stack for the **Quantiacs Q25 Crypto Top-10 Long** contest. The objective is not “find one pretty Sharpe and tune it until green.” We build a small portfolio of **distinct, falsifiable mechanisms** using Quantiacs-provided data only, then try to kill them with causality, cost, drawdown, fold, correlation and multipass tests.

> **Evidence boundary:** historical numbers in the Top 10 below are frozen local research / execution-translation evidence through **2026-08-20**. They are **not current official Quantiacs scores, forecasts, or promises of live performance**. Current platform cleaner/checker, multipass, liquidity/runtime and external-correlation checks remain mandatory.

### Public research site

The GitHub Pages surface at **https://svyable.github.io/quantiacs-q25/** is deliberately a **showcase, not a second source of truth**. It should explain what the lab is doing, why the mechanisms differ, what evidence exists, what remains PENDING, and how cost/causality/originality gates work. Measured results are recorded in repository artifacts first; Pages may summarize them only after the exact strategy/run is traceable. Deployment details live in [docs/PAGES.md](docs/PAGES.md).

### Explore

[**🌐 Q25 Quant Lab**](https://svyable.github.io/quantiacs-q25/) · [**Local Research Access**](docs/LOCAL_RESEARCH_ACCESS.md) · [**Frontier Iteration Engine**](docs/FRONTIER_ITERATION.md) · [**Strategy Generation Playbook**](docs/STRATEGY_GENERATION_PLAYBOOK.md) · [**Next-Agent Prompt**](docs/AGENT_PROMPT.md) · [**Research Frontier YAML**](configs/research_frontier.yaml) · [Quant Research Showcase source](docs/index.md) · [Strategy Atlas](docs/STRATEGY_ATLAS.md) · [Research Method](docs/RESEARCH_METHOD.md) · [Testing Pyramid](docs/TESTING_PYRAMID.md) · [Historical Top-10 YAML](configs/historical_top10.yaml)

The `docs/` site is built with Jekyll from [`docs/_config.yml`](docs/_config.yml) and deployed by [`.github/workflows/pages.yml`](.github/workflows/pages.yml).

---

## Historical top ten

Frozen research-preparation roster assembled from our prior Q25 campaigns. Baseline research friction was `4% × ATR(14)` per unit of position change; the stress column shows the larger ATR fraction used for each row.

| # | Strategy | Mechanism / role | Full SR | Max DD | Stress SR | Stress | Research status |
|---:|---|---|---:|---:|---:|---:|---|
| 1 | **V10 multi-factor ensemble — Pareto** | primary legacy factor / residual core | **2.261** | -30.90% | **1.965** | 12% ATR | prepare / precheck |
| 2 | **V11 new-only event ensemble — Balanced** | seesaw + motif + lifecycle + calendar | 1.261 | -23.11% | 0.899 | 12% ATR | prepare / precheck |
| 3 | **C165 mobility / consensus risk** | short/medium consensus-risk blend | 1.230 | -21.45% | 0.934 | 12% ATR | adapter + precheck |
| 4 | **V12 signed volume diffusion — 50/50 bridge** | abnormal volume → residual-return network | 1.035 | -33.86% | 0.750 | 12% ATR | exact official `>1` gate required |
| 5 | **Co-crash shelter — base 126D** | defensive crash-comovement selection | 1.772 | -14.38% | 1.627 | 12% ATR | adapter + precheck |
| 6 | **Residual dispersion switch** | sparse idiosyncratic dispersion timing | 1.536 | -12.00% | 1.410 | 8% ATR | prepare / precheck |
| 7 | **Breadth Thrust Switch** | breadth acceleration / market-state timing | 1.185 | -21.49% | 1.075 | 8% ATR | prepare / precheck |
| 8 | **Slow defensive factor balance** | diversified slow factor mix | 1.526 | -24.72% | 1.445 | 8% ATR | prepare / precheck |
| 9 | **126D positive-return consistency — five names** | persistent-trend reserve | 1.700 | -24.84% | 1.538 | 12% ATR | conditional reserve |
| 10 | **V5 latency ensemble** | multi-speed low-risk V10-family alternate | 2.105 | **-10.30%** | 1.830 | 12% ATR | conditional reserve |

**Do not read this as ten independent alphas.** V10–V9 historical matched correlation was ~0.9998, C165–R002 ~0.9983, and V10–V5 ~0.9156. High-performing aliases inside one lineage get one conceptual slot, not fake diversification.

Full mechanism cards, caveats and historical source provenance live in the [Strategy Atlas](docs/STRATEGY_ATLAS.md).

---

## The four-core research graph

The strongest frozen core is **V10 + V11 + C165 + V12**. Their matched local daily streams over 2022-01-01 → 2026-08-20 were materially less correlated than many reserves:

| | V10 | V11 | C165 | V12 |
|---|---:|---:|---:|---:|
| **V10** | 1.000 | 0.288 | 0.329 | 0.398 |
| **V11** | 0.288 | 1.000 | 0.334 | 0.414 |
| **C165** | 0.329 | 0.334 | 1.000 | 0.281 |
| **V12** | 0.398 | 0.414 | 0.281 | 1.000 |

Those are historical diagnostics—not sponsor uniqueness approvals—but they capture the design principle: **new alpha means a new return mechanism, not a new filename**.

### What those four actually do

- **V10** — high-capacity multi-factor anchor: residual/factor information, defensive sleeves, state routing, caps and cash.
- **V11** — clean-slate event alpha: directed negative cross-crypto shock propagation, seven-day price/volume motifs, liquidity lifecycle events and sparse calendar recurrence.
- **C165** — risk efficiency: blend fast anchor evidence with a small medium-horizon market-consensus component rather than adding another raw momentum score.
- **V12** — structural information flow: abnormal volume in one asset is mapped through a causal directed network to next-day residual-return expectations in other assets.

---

## SOTA operating system

```text
mechanism hypothesis
      ↓
causal implementation + static audit
      ↓
prefix invariance / no-lookahead replay
      ↓
chronological discovery → validation folds
      ↓
cost ladder + turnover + liquidity stress
      ↓
residualization against incumbent return streams
      ↓
multiple-testing / PBO / deflated-Sharpe diagnostics
      ↓
Pareto promotion: return × DD × costs × originality
      ↓
current Quantiacs cleaner + multipass + correlation
      ↓
only then: live-entry candidate
```

### Discovery track

High-capacity alpha factory across breakout, flow, tail, residual momentum, dispersion, breadth, lifecycle, lead/lag, higher moments and regime-conditioned mechanisms.

### Robustness track

Fewer bounded signals, slower/controlled turnover, cash allowed, capped allocation, no hand-picked assets, direct stress tests. The existing [`robust_weekly_waterfill.py`](strategies/robust_weekly_waterfill.py) is the simplest reference implementation.

### Convergence is evidence

When the discovery track and robustness track independently point at the same mechanism, confidence rises. When a “new” strategy only reproduces an incumbent return stream, it does not matter how attractive the headline backtest looks.

---

## New synthesis: `q25_sota_meta_ensemble_v1`

[`strategies/q25_sota_meta_ensemble.py`](strategies/q25_sota_meta_ensemble.py) is a **new PENDING research strategy** that combines the best mechanism classes without claiming historical champion parity:

1. **market-residual momentum** — continuation after removing the common crypto factor;
2. **causal abnormal-volume response** — estimate prior-volume → next-residual-return response and apply it to current shocks;
3. **co-crash safety** — prefer names with lower common crash-state dependence;
4. **low residual skewness** — higher-moment satellite inspired by the V13 seam;
5. **path-efficient trend** — reward directional movement that required less noisy travel;
6. **breadth / trend / volatility regime gating** — decide gross risk at the universe level;
7. **inverse-risk capped water-fill** — long-only, cash allowed, internal 25% name cap, unit-gross ceiling.

It uses only Q25-compatible OHLCV + historical `is_liquid`, contains no coin identities, and carries **no performance claim** until it survives the full testing pyramid. The historical Top-10 numbers above **do not attach to this implementation**.

---

## Frontier lab

We keep failed or conditional research visible because the rejection reason is valuable information.

- **V13 low residual-skew** found an interesting higher-moment seam with historical SR 1.446 and 12%-ATR stress SR 1.303, but maximum drawdown reached **-62.38%**. Under the newer internal drawdown discipline it stays outside the current top ten.
- **Market-assimilation delay acceleration** produced sparse candidates that passed many performance/cost/activity gates but breached the frozen recent-correlation ceiling. Lead, not admission.
- **VIPER–HELIOS** contributed reusable architecture—causal IC weighting, covariance shrinkage, equal-risk contribution, multi-horizon momentum, ATR-aware no-trade regions and crash overlays. Architecture can migrate; old metrics cannot.

See [docs/index.md](docs/index.md) for the full public research narrative.

---

## Next agent: generate frontier strategies, then measure them

The next strategy agent should start with [`AGENTS.md`](AGENTS.md), [Local Research Access](docs/LOCAL_RESEARCH_ACCESS.md), the [Strategy Generation Playbook](docs/STRATEGY_GENERATION_PLAYBOOK.md) and [`configs/research_frontier.yaml`](configs/research_frontier.yaml), **before** opening the old seed factory.

Default cadence:

```text
map incumbents
→ generate 24 hypotheses across multiple frontier areas
→ score novelty/falsifiability before returns
→ preregister 6
→ implement up to 3 under strategies/generated/
→ run them with public/default Quantiacs access
→ produce measured fold + cost + drawdown + turnover evidence
→ run L0–L9 + falsifiers + residual tests
→ promote / reserve / kill
```

A missing personal credential is **not** permission to stop at code generation. The agent should dogfood the local evaluator with `API_KEY=default` and report actual metrics whenever the toolbox/data endpoint is reachable. Account-bound remote correlation and submission can remain `PENDING` until authenticated.

Current preferred frontiers include **on-chain state (conditional on Q25 admissibility), forecast surprise/disagreement, price-volume elasticity, index ecology (conditional on admissibility), assimilation-delay dynamics, correlation-topology change, liquidity-transition hysteresis, volatility term structure, tail dependence, range-volume geometry, shock-recovery surfaces, nonlinear response, opportunity density, and execution-aware alpha density**.

The novelty rule is intentionally strict: a proposed independent alpha should differ from its nearest incumbent on at least **two** of information primitive, transform, timing/state, and portfolio construction. Otherwise label it as a refinement or ablation.

---

## Contest facts

| Item | Value |
|---|---|
| Contest | Q25 Crypto Top-10 Long |
| `competition_type` | `crypto_daily_long` |
| Data | `qndata.cryptodaily_load_data` + `is_liquid` |
| Side | Long-only |
| IS start | `2016-01-01` |
| Hard gate | **IS Sharpe > 1.0** |
| Entry deadline | **2026-09-30** |
| Live evaluation | **2026-10-01 – 2027-01-31** |

Rules snapshot: [`configs/rules_snapshot.yaml`](configs/rules_snapshot.yaml). Re-verify platform rules immediately before any submission.

---

## Install

```bash
conda install -c quantiacs-source qnt
# or
pip install "git+https://github.com/quantiacs/toolbox.git"
pip install -r requirements.txt
```

You do **not** need a personal Quantiacs key for the local/public research path.
The harness automatically sets `API_KEY=default` if no key exists. If you want an
explicit `.env`, copy `.env.example`; it already contains the public sentinel.

```bash
cp .env.example .env   # optional; API_KEY=default
```

A real participant key should stay private and is only needed for authenticated,
account-bound platform operations.

## Run

```bash
# No personal credential required.
python scripts/run_strategy.py strategies/robust_weekly_waterfill.py
python -m research.iteration --budget 18

# New multi-mechanism synthesis.
python scripts/run_strategy.py strategies/q25_sota_meta_ensemble.py

# Create a preregistered experiment.
python scripts/new_experiment.py --track discovery --mechanism correlation_topology

# Old deterministic factory is primarily plumbing/control infrastructure.
python scripts/bootstrap_ideas.py
python scripts/run_factory.py --top-n 3 --mutants 2 --seed 42
```

For a standalone script that imports `qnt` before using this repo's runner:

```bash
API_KEY=default python path/to/strategy.py
```

---

## Repository map

```text
AGENTS.md       first-read agentic research contract
docs/           access guide, Pages site, frontier engine, showcase, atlas, playbook, method, pyramid
configs/        rules, historical top-10, research frontier, external leads, gates, costs, regimes, folds
factory/        desks, expanded mechanism catalog, tracks, render, gates, evolve, runner
research/       executable frontier iteration, benchmark, static audit, prefix tests, preregistration
strategies/     baselines + frozen champion mirrors + PENDING/new work in generated/
experiments/    append-only experiment directories / ledgers
results/        measured outputs only; no invented metrics
templates/      preregistration, ledger, PM report, hosted strategy notebook
```

## Evidence labels

- **Historical research** — frozen evidence from a dated prior campaign.
- **Observed local / public-default** — real Quantiacs-toolbox measurements produced locally with `API_KEY=default`; not account-bound platform clearance.
- **Prepare / precheck** — worthy of current official verification; not approved yet.
- **Conditional reserve** — strong result with overlap, packaging or evidence limitations.
- **PENDING** — a specific layer has genuinely not run or could not run; do not use “no personal key” as the reason for local-toolbox PENDING.

## Non-negotiables

- No invented Sharpe, return or drawdown figures.
- No future leakage, centered windows, hidden negative shifts or manual coin picks.
- Quantiacs-provided strategy fields only.
- Cash is a legitimate position.
- Cost and turnover are first-class objectives.
- Correlation / residual-alpha checks are promotion gates, not reporting decorations.
- Previously observed 2025 / preview periods are diagnostics, not magically fresh OOS data.
- A strategy can be rejected even when its equity curve looks spectacular.
- **Dogfood the evaluator:** if local/public Quantiacs data are reachable, measure the candidate instead of leaving it unrun.

**The goal is not ten submissions. The goal is the smallest set of causal, distinct, cost-aware mechanisms that can survive the live window.**
