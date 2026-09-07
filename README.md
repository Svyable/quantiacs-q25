# quantiacs-q25 — Research & Validation for Quantiacs Q25

**Philosophy:** Q25 is **research-and-validation**, not “write strategy, maximize Sharpe, tweak until green.”  
Target **causal, unique, low-cost** mechanisms with a credible chance of **positive Sharpe** on the unseen live window (**2026-10-01 → 2027-01-31**). Prefer **residual / unique alpha** over high-Sharpe clones. Never ask “How can I increase this backtest?” before “What independent mechanism have we not tested, and what would falsify it?”

**Dual tracks (both required):**  
**(A) discovery** — high-capacity alpha factory (ensembles: breakout, flow, tail, risk-guards).  
**(B) robustness** — few bounded signals, weekly rebalance, cash allowed, capped water-fill, no hand-picked assets.  
When both tracks independently converge on the same mechanism → stronger evidence.

**Honesty:** this repo does **not** claim backtest numbers. Metrics enter `results/` / `experiments/` only after a real `qnt` or hosted run. Unrun = **PENDING**. Desk names evoke styles from known shops as **idea generators only** — **no affiliation**.

**API_KEY required.** Blank/empty does **not** work — the toolbox exits. Free profile key: [Quantiacs personal page](https://quantiacs.com/personalpage/homepage). Copy `.env.example` → `.env` or `export API_KEY=...`.

Remote: `https://github.com/Svyable/quantiacs-q25`

---

## Docs (start here)

| Doc | Purpose |
|-----|---------|
| [docs/RESEARCH_METHOD.md](docs/RESEARCH_METHOD.md) | Operating system: layers, objective, dual tracks, iteration loop, behavioral rules |
| [docs/TESTING_PYRAMID.md](docs/TESTING_PYRAMID.md) | Levels 0–9 concrete checks |
| [docs/AGENT_PROMPT.md](docs/AGENT_PROMPT.md) | Paste-ready master prompt (§0–27) |
| [docs/SUBMISSION_CHECKLIST.md](docs/SUBMISSION_CHECKLIST.md) | Hosted `strategy.ipynb` workflow |

## Contest facts (hard)

| Item | Value |
|------|--------|
| Contest | Q25 Crypto Top-10 Long |
| `competition_type` | `crypto_daily_long` |
| Data | `cryptodaily_load_data` + `is_liquid` |
| Side | Long-only |
| IS start | `2016-01-01` |
| Hard gate | **IS Sharpe > 1.0** (not 0.7) |
| Deadline | 2026-09-30 |
| Live | 2026-10-01 – 2027-01-31 |

See `configs/rules_snapshot.yaml` (dated 2026-09-07).

## Install

```bash
conda install -c quantiacs-source qnt
# or: pip install "git+https://github.com/quantiacs/toolbox.git"
pip install -r requirements.txt
cp .env.example .env   # set API_KEY=
```

## Quick start

```bash
export API_KEY=...   # required
python scripts/run_strategy.py strategies/baseline_sma_rsi.py
python scripts/new_experiment.py --track robustness --mechanism sma_trend_waterfill
python scripts/bootstrap_ideas.py
python scripts/run_factory.py --top-n 3 --mutants 2 --seed 42
```

Hand baselines: `baseline_sma_rsi`, `trend_momentum`, `mean_reversion`, `vol_scaled_trend`, plus robustness-track `robust_weekly_waterfill` (no metrics claimed).

## Layout

```
docs/           research method, pyramid, agent prompt, submission checklist
configs/        rules snapshot, promotion gates, cost ladder, regimes, folds
factory/        desks, mechanisms, tracks, render, gates, evolve, runner
research/       L0/L1 static audit, L2 prefix, preregister
strategies/     hand + generated + robust_weekly_waterfill
experiments/    append-only experiment dirs / ledgers
templates/      preregistration, ledger, pm_report, strategy.ipynb
```

## Soft cook (aspirational — NOT claimed)

`configs/targets.yaml`: Sharpe ≥ 2, |DD| ≤ 0.40, equity growth factor ≥ 100. Never treat as achieved until a real backtest.

## Notes

- Do not invent Sharpe / return / DD figures.
- Quantiacs-provided fields only in strategies.
- Promotion soft thresholds in `configs/promotion_gates.yaml` are **TODO for the human**.
