# Strategy Generation Playbook — Q25

This document is for the **next research agent whose job is to create new strategies**, not merely rerun incumbents.

The repo already contains strong historical families. Your job is to extend the frontier **without wasting research budget on near-duplicates**.

Start here, then read:

1. `configs/rules_snapshot.yaml`
2. `configs/historical_top10.yaml`
3. `configs/research_frontier.yaml`
4. `docs/STRATEGY_ATLAS.md`
5. `docs/TESTING_PYRAMID.md`
6. `configs/promotion_gates.yaml`

Do not begin with `factory/desks.py` and blindly emit old SMA/RSI ideas. Those are controls and plumbing tests, not the current frontier.

---

## 1. Your mission

Produce **causal, asset-agnostic, Quantiacs-data-only strategies** that have a plausible mechanism not already represented by the incumbent roster.

A successful campaign is not “the highest Sharpe I could find.” It is a campaign where:

- the mechanism was specified before expensive testing;
- the nearest incumbent was named explicitly;
- the proposal differs materially from that incumbent;
- falsifiers and ablations were predeclared;
- the code is causal and reproducible;
- cost, drawdown, fold and originality evidence are all recorded;
- failed ideas remain in the ledger;
- the live window is not used for selection.

The best outcome may be **no promotion** if the new family does not survive.

---

## 2. First-hour protocol

Before writing a strategy file, do this in order.

### A. Build an incumbent map

Read `configs/historical_top10.yaml` and write a short scratch table with:

- strategy id;
- information primitive;
- transform;
- timing/state condition;
- allocator/risk construction;
- known overlap notes.

Use the four novelty axes from `configs/research_frontier.yaml`:

1. **information primitive** — what raw causal object is measured?
2. **transform** — how is it turned into a score?
3. **timing/state condition** — when is it allowed to matter?
4. **portfolio construction** — how does it become risk?

A candidate should differ from the nearest incumbent on **at least two axes** to count as a new alpha hypothesis. One-axis changes are ablations or refinements.

### B. Generate 24 hypotheses before backtesting

Default campaign cadence:

- **24** mechanism sketches;
- score them without performance data;
- preregister the best **6**;
- implement the best **3**;
- run the pyramid;
- promote zero, one, or more only if gates support it.

This prevents the first plausible idea from consuming the whole campaign.

### C. Score ideas before seeing returns

For each sketch, score 0–2 on:

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| Novelty | same family | one meaningful axis new | ≥2 novelty axes new |
| Causal clarity | vague | plausible | exact decision-time construction |
| Falsifiability | no clean test | weak falsifier | direct destructive falsifier |
| Parameter economy | >5 free knobs | 4–5 | ≤3 initial free knobs |
| Cost plausibility | likely churn | uncertain | naturally persistent / sparse |
| Portfolio complement | clone-like | unclear | clear missing portfolio role |

Do **not** score historical Sharpe at this stage.

Pick the six highest-quality hypotheses, not six variations of one theme.

---

## 3. The current incumbent map

The exact historical evidence is in `configs/historical_top10.yaml`; this table is only a mechanism map.

| Incumbent | What is already occupied |
|---|---|
| V10 | mature multi-factor trend / residual / defensive routing |
| V11 | shock-network, short motif, liquidity lifecycle, sparse calendar event mix |
| C165 | fast/medium market-consensus risk timing |
| V12 | abnormal-volume → next residual-return directed diffusion |
| CoCrash126 | crash-comovement defense |
| Residual dispersion switch | residual-dispersion state timing |
| Breadth | breadth acceleration / market-level risk gate |
| Factor balance | slow defensive factor mix |
| Trend_hit126 | persistent positive-return consistency |
| V5 latency | multi-speed routing inside the V10 lineage |
| V13 frontier | low residual skewness, but unacceptable historical path risk under newer discipline |
| SOTA meta-ensemble | residual momentum + volume response + co-crash + low residual skew + path-efficient trend + regime gating |

### Translation rule

If your proposal can be described as “the same row above, but with a new lookback / threshold / blend weight / top-K / rebalance day,” it is **not a new strategy family**.

It may still be useful as an ablation or robustness check. Label it correctly.

---

## 4. Preferred frontier directions

Use `configs/research_frontier.yaml` as the machine-readable source. Current high-priority spaces include:

### 4.1 Assimilation-delay dynamics

Ask **how quickly** assets absorb common-market or cross-asset shocks and how that speed changes.

Potential primitives:

- lag-response share across 0–3 days;
- change in median response lag;
- leader/follower turnover;
- cohort-level lag compression;
- acceleration/deceleration of information assimilation.

Do not simply retune prior rejected delay candidates. Build a new observable or new state interpretation.

### 4.2 Correlation-topology change

Use the *structure* of the residual correlation graph rather than static correlation magnitude.

Examples:

- centrality migration;
- bridge-node emergence;
- cluster fragmentation;
- eigenvalue concentration change;
- sudden correlation breakdown/reconnection;
- sector-like community persistence inferred only from the eligible crypto cross-section.

A static low-correlation or low-beta sort is not enough.

### 4.3 Liquidity-transition hysteresis

Treat `is_liquid` history as a state process.

Questions:

- Is age-since-entry predictive after controlling for trend?
- Does re-entry behave differently from first entry?
- Does repeated boundary-crossing signal instability?
- Is there a causal “eligibility maturation” curve?

Do not duplicate V11's simple positive-entry lifecycle sleeve.

### 4.4 Volatility term structure

Go beyond inverse-vol sizing.

Study:

- 7/21/63/126-day realized-vol curve shape;
- short-vol / long-vol acceleration;
- volatility-of-volatility;
- cross-sectional vol compression/expansion;
- whether curve shape predicts return, recovery, or safe gross deployment.

The alpha question is about **shape and change**, not “high volatility is bad.”

### 4.5 Tail-dependence state

Go beyond V13 skew and CoCrash126.

Candidate primitives:

- downside co-exceedance frequency;
- conditional semivariance;
- drawdown duration and recovery asymmetry;
- lower-tail rank dependence;
- crash breadth conditional on asset-specific stress;
- robust quantile-state transitions.

### 4.6 Range-volume geometry

Use interactions among OHLC range, close location, volume shock and path shape.

Examples:

- range expansion with low close-location efficiency;
- abnormal volume conditional on where the close sits inside the daily range;
- compression → expansion state transition with residual confirmation;
- multi-day path curvature rather than a single candle rule.

### 4.7 Shock-recovery surface

Model *how* recovery unfolds after a defined shock.

Features can include:

- shock depth;
- time since shock;
- recovery slope;
- failed-recovery count;
- market-vs-idiosyncratic shock classification;
- breadth of concurrent recovery;
- relative recovery ordering across assets.

Blind “buy the dip” is not the hypothesis.

### 4.8 Nonlinear cross-sectional response

Move beyond linear V12-style diffusion.

Research:

- sign asymmetry;
- threshold response;
- saturation;
- state-dependent leader reliability;
- lag compression;
- conditional cohort response.

Keep the model interpretable enough to falsify.

### 4.9 Opportunity density

Predict **whether there is enough independent cross-sectional opportunity to trade at all**.

Possible measures:

- score dispersion;
- rank stability;
- leader turnover;
- disagreement between independent mechanism families;
- residual-alpha breadth;
- concentration of opportunity in one or two names.

This is a cash-allocation mechanism, not a future-return oracle.

### 4.10 Execution-aware alpha density

Ask whether a signal is strong **relative to its ATR-linked cost of acting now**.

Examples:

- expected signal change / ATR cost proxy;
- persistence-conditioned no-trade threshold;
- trade only when score improvement exceeds state-dependent cost;
- compare delayed execution vs immediate execution as a falsifier.

Do not add smoothing after the fact and call that a new alpha.

---

## 5. Candidate design contract

Every preregistered candidate must answer this template.

```text
ID:
Track: discovery | robustness
Mechanism family:
One-sentence thesis:
Raw information primitive:
Transform into score:
Decision-time availability:
Timing / state condition:
Selection rule:
Allocation rule:
Cash rule:
Rebalance rule:
Maximum initial free parameters: <= 3
Nearest incumbent:
Novelty axes changed:
Why this is not just an incumbent variant:
Primary falsifier:
Ablation:
Expected failure mode:
Cost hypothesis:
Portfolio role if it works:
```

If any of these are blank, the idea is not ready to backtest.

---

## 6. Parameter discipline

The easiest way to overfit Q25 is to let a reasonable mechanism become a large tuning surface.

### Initial implementation

Use at most **three free parameters**. Prefer economically interpretable horizons such as 21 / 63 / 126 / 252 when appropriate, but do not assume those are optimal.

### First grid

Use coarse, predeclared values that test **mechanism stability**, not maximum score.

Good question:

> Does this mechanism work across short / medium / long versions?

Bad question:

> Which of 87 nearby lookbacks maximizes full-period Sharpe?

### Plateau rule

Prefer an interior, stable plateau over a boundary maximum. If only one narrow point works, treat the mechanism as fragile until forward evidence says otherwise.

### No reveal-driven repair

Once a validation or diagnostic window has been inspected, do not tune directly to repair that miss and continue calling the same experiment clean. Open a new, explicitly contaminated/refinement experiment and preserve the original result.

---

## 7. Falsification before optimization

A strategy should be easier to disprove than to explain away.

Useful falsifiers:

- sign inversion;
- lag shuffle;
- leader/follower shuffle;
- state-mask inversion;
- random matched-frequency event dates;
- replace the proposed primitive with a volatility-matched noise/control primitive;
- remove residualization and test whether the “new” alpha collapses into market trend;
- replace the special allocator with equal weight to see whether the edge lives in alpha or sizing;
- delay the signal an extra bar;
- perturb the universe history without changing current membership to test lifecycle dependence.

A failed falsifier is a **kill**, not a reason to invent a new story.

---

## 8. Originality test hierarchy

Do not wait until the end to discover a clone.

### Before backtest

Nearest-incumbent novelty comparison on the four axes.

### During local research

Compare matched return streams against:

- V10 family;
- V11;
- C165 family;
- V12;
- CoCrash / dispersion / breadth controls;
- simple liquid equal-weight / trend controls.

### Residual test

A candidate with good raw Sharpe but no residual value after explaining it with incumbents is a **portfolio refinement**, not a new alpha.

### Correlation failure rule

Do not respond to a correlation failure by optimizing blend weights against the failed strategy until it barely passes. That changes the question from “is this new alpha?” to “can I game the boundary?” — reject that workflow.

---

## 9. Campaign structure

Use three passes.

### Pass 1 — mechanism screen

Cheap, broad, intentionally rough.

Goal: determine whether the sign and basic mechanism are plausible.

Record:

- causal compile/static checks;
- rough full-period behavior;
- gross/activity;
- obvious overlap;
- falsifier direction.

Do not promote here.

### Pass 2 — exact research

Only for candidates that survive Pass 1.

Run:

- exact Quantiacs-style stats;
- prefix invariance;
- chronological folds;
- cost ladder;
- drawdown/tail diagnostics;
- turnover/activity;
- residual/originality tests;
- preregistered falsifier and ablation.

### Pass 3 — portfolio admission

Ask a different question:

> Does adding this strategy improve the active slate enough to deserve operational complexity?

Test marginal portfolio contribution, not just standalone metrics.

A candidate can be a good standalone strategy and still fail portfolio admission.

---

## 10. Kill rules

Kill or freeze a candidate when any of these happens:

- future leakage or prefix failure;
- non-liquid or negative exposure;
- mechanism falsifier passes;
- only one narrow parameter point works;
- performance vanishes under reasonable cost;
- severe path risk violates current policy;
- no residual value versus the nearest incumbent;
- the candidate exists mainly because a previously observed diagnostic period was tuned around;
- external/current correlation rejects it;
- implementation cannot reproduce its own research weights.

Do not delete failed work. Preserve the reason.

---

## 11. Code-generation rules

For every new strategy:

- keep it under `strategies/generated/` until promoted;
- put the experiment id and preregistration hash in the module docstring;
- state `PENDING` until a real run writes metrics;
- use only Quantiacs strategy data;
- use historical `is_liquid`, never a static symbol list;
- no negative shift, centered rolling, or future-index tricks;
- keep `strategy(data) -> weights` simple;
- keep reporting code separate from signal code;
- preserve cash when the signal or allocation capacity is weak;
- use deterministic tie-breaking;
- make risk caps explicit constants;
- make the execution assumption explicit;
- expose enough intermediate logic to audit the mechanism.

A complicated strategy whose causal path cannot be explained in a few paragraphs is not ready for the contest.

---

## 12. What to produce at the end of a campaign

A useful agent run should leave the repo with:

1. **idea slate** — all 24 sketches with pre-backtest novelty scores;
2. **6 preregistrations** — hashed before deeper testing;
3. **up to 3 implementations** — generated strategy files;
4. **results for every run actually executed** — no invented fields;
5. **kill ledger** — explicit failure reasons;
6. **PM report** — observed vs PENDING clearly separated;
7. **portfolio admission recommendation** — promote / reserve / kill / needs-forward-evidence;
8. **next frontier note** — what was learned about the mechanism even if nothing passed.

Do not optimize for the number of files created. Optimize for **information gained per research look**.

---

## 13. A good next campaign

A strong next agent should probably **not** start with another momentum blend.

A better opening slate would intentionally span different objects, for example:

- 6 assimilation-delay / response-timing hypotheses;
- 5 correlation-topology hypotheses;
- 4 liquidity-transition hypotheses;
- 4 volatility-term-structure hypotheses;
- 3 tail-dependence hypotheses;
- 2 execution-aware opportunity-density hypotheses.

Then select the best six by novelty + falsifiability **before seeing returns**.

This is a research program. The next breakthrough is more likely to come from a **new measurable object** than from another optimized combination of signals we already understand.
