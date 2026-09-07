# quantiacs-q25 — Q25 Crypto Top-10 Long strategy factory

Greenfield quant-shop style **agentic strategy factory** for the Quantiacs
**Q25 Crypto Top-10 Long** contest. Desk names evoke styles from well-known
quant shops (AQR / WorldQuant / Jump / Two Sigma / Point72 / Cumberland / DRW)
as **idea generators only** — this project claims **no affiliation**.

**Honesty:** this repository does **not** claim any backtest numbers. Soft
“cook” targets are aspirational research goals. Hard contest gates are encoded
from published rules. Metrics appear in `results/registry.jsonl` only after a
real `qnt` run.

Target remote (parent pushes; do not push from this box by default):
`https://github.com/Svyable/quantiacs-q25`

---

## Contest facts (encoded)

| Item | Value |
|------|--------|
| Contest | Q25 Crypto Top-10 Long |
| `competition_type` | `crypto_daily_long` |
| Data | `qndata.cryptodaily_load_data` + field `is_liquid` |
| Side | Long-only |
| In-sample start | `2016-01-01` |
| Hard gate | **IS Sharpe > 1.0** (arithmetic crypto Sharpe). Library soft checks may use ~0.7 — **use 1.0 for contest**. |
| Deadline | 2026-09-30 |
| Live | 2026-10-01 – 2027-01-31 |
| Official pattern | [Q24 Crypto Guide](https://quantiacs.com/documentation/en/examples/q24_crypto_guide.html) |

---

## Soft cook targets (aspirational — NOT claimed)

Configured in `configs/targets.yaml`:

- Sharpe ≥ 2.0
- Max drawdown ≤ 40% (`|max_drawdown| ≤ 0.40`)
- Equity growth factor ≥ **100** (Quantiacs equity is a growth factor: **100x ≈ +9900% ≈ “10000%”** return target)

Never treat these as achieved results until a real backtest fills the registry.

---

## Install

### 1. Quantiacs toolbox

```bash
# conda
conda install -c quantiacs-source qnt

# or pip
pip install "git+https://github.com/quantiacs/toolbox.git"
```

Also: `pip install -r requirements.txt` for factory YAML helpers (PyYAML, etc.).

### 2. API key (required)

**Empty / blank `API_KEY` does NOT work.** The toolbox exits if `API_KEY` is `''`.

1. Create a **free** Quantiacs account.
2. Copy your **profile key** from
   [https://quantiacs.com/personalpage/homepage](https://quantiacs.com/personalpage/homepage)
3. Configure:

```bash
cp .env.example .env
# edit .env: API_KEY=your_key_here

# or
export API_KEY=your_key_here
```

Strategy scripts and `factory/runner.py` fail clearly if the key is missing.

---

## Day-one: run a baseline strategy

```bash
cd /path/to/quantiacs-q25
export API_KEY=...   # required
python scripts/run_strategy.py strategies/baseline_sma_rsi.py
```

Or run a module directly:

```bash
python strategies/baseline_sma_rsi.py
```

Hand-written baselines (multipass + `load_data`):

- `strategies/baseline_sma_rsi.py` — official Q24 SMA/RSI liquid long pattern
- `strategies/trend_momentum.py` — breakout / trend
- `strategies/mean_reversion.py` — RSI / Bollinger long-only
- `strategies/vol_scaled_trend.py` — inverse-vol scaled trend

Multipass pattern used throughout:

```python
def load_data(period):
    return qndata.cryptodaily_load_data(tail=period)

def strategy(data):
    ...
    return weights  # long-only, * is_liquid; last-day slice for multipass

weights = qnbt.backtest(
    competition_type="crypto_daily_long",
    load_data=load_data,
    lookback_period=365,
    start_date="2016-01-01",
    strategy=strategy,
    analyze=True,
    check_correlation=True,
)
```

For multipass, strategies return **last-day** weights (`.isel(time=-1)` when a
time dimension remains). The official guide also documents **single-pass** over
the full series for faster iteration.

---

## Factory loop

```bash
# 1) Seed idea ledger + registry placeholders
python scripts/bootstrap_ideas.py

# 2) One evolution generation (mutate / grid / render under strategies/generated/)
python scripts/run_factory.py --top-n 3 --mutants 2 --seed 42

# 3) After a real backtest, parse stats into gates (no fabricated metrics):
#    from factory.gates import parse_stats, evaluate_all
```

Architecture:

```
configs/          hard contest rules + soft cook targets
factory/desks.py  style desks + alpha families (idea generators)
factory/ideas.py  Idea dataclass + seed library
factory/render.py Idea -> strategies/generated/*.py
factory/gates.py  hard (Sharpe_IS > 1.0) + soft cook gates
factory/registry.py  JSONL run ledger (metrics placeholders OK)
factory/evolve.py mutate / grid / rank hooks (LLM hook stubbed)
factory/runner.py subprocess runner (requires API_KEY)
```

v1 evolution is **deterministic mutation + ranked parameter search** (no LLM).
`expand_with_llm()` is a hook for later.

---

## Gates

**Hard** (`configs/contest_q25.yaml`):

- `sharpe_is > 1.0`
- long-only
- liquid-only (`is_liquid`)

**Soft cook** (`configs/targets.yaml`) — aspirational only:

- Sharpe ≥ 2, `|DD|` ≤ 0.40, equity ≥ 100

---

## Layout

See the repository tree under this README. Generated strategies land in
`strategies/generated/` (gitignored except `.gitkeep`). Results ledger:
`results/registry.jsonl`.

---

## Notes

- Do not invent or commit fabricated Sharpe / return / drawdown figures.
- Only Quantiacs-provided data fields are used in strategies.
- Svyable has prior Quantiacs contest experience (e.g. Q23); this repo is a
  fresh Q25 factory and does not restate past scores as Q25 results.
