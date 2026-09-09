# External Research Leads — Q24/Q25 Public Intelligence

**Purpose:** give the next research agent the useful parts of the public Q24/Q25 internet sweep without forcing it to repeat the reconnaissance or accidentally treat internet claims as validated evidence.

This document is a **research-intelligence memo**, not a performance registry.

The operating rule is simple:

> Borrow mechanisms, experimental structure, and data ideas. Reproduce everything else from scratch.

Public code can be wrong. Public backtests can be incomparable. Leaderboard names can be misleading. Current preview/OOS statistics can be almost meaningless when only a few post-submission days exist. Nothing in this memo bypasses preregistration, causality, cost, fold, residual, correlation, multipass, cleaner or submission gates.

Machine-readable companion: [`configs/external_research_leads.yaml`](../configs/external_research_leads.yaml).

---

## 1. What the public sweep actually found

The internet did **not** reveal a magical source file for the Q24 winner or the current Q25 leaderboard leader.

It did reveal five useful categories of information:

1. an underused **Quantiacs-provided blockchain data primitive** demonstrated in the official Q24 crypto guide;
2. a public Q25-style **stateful predictive-coding** implementation suggesting forecast-error / surprise as a different information object;
3. current Q25 leaderboard titles suggesting active experimentation with **rolling classifiers, elasticity, Markov/regime models, correlation clusters, range continuity and low-volatility**;
4. public Q25 code where **very simple persistent low-volatility selection** reportedly beat its own more conventional momentum controls in a local 2024–2025 experiment;
5. the Q24 winner's public profile showing that an eventual winning contest outcome can coexist with **extremely low average turnover**.

The strongest new directions for us are therefore not “copy a public strategy.” They are:

- **on-chain state × cross-sectional crypto behavior**;
- **online forecast surprise / model disagreement**;
- **price-volume elasticity / absorption geometry**;
- **benchmark-composition ecology / market-cap migration**, if current Q25 admissibility is confirmed.

---

## 2. Evidence hierarchy for internet material

Treat external discoveries in four levels.

### Level A — official Quantiacs rule/documentation evidence

Useful for understanding platform capabilities, contest rules, loaders and execution patterns.

Still re-verify anything contest-specific before submission.

### Level B — official Quantiacs example code

Useful for API mechanics, rolling retraining patterns and supported interfaces.

It is **not** evidence that the example's model contains alpha.

### Level C — third-party public source code

Useful as an idea generator and implementation reference.

Assume it may contain:

- weak or incompatible costs;
- survivorship mistakes;
- symbol-specific logic;
- full-history tuning;
- leakage;
- stale competition rules;
- incomparable performance conventions.

Audit before borrowing even one line.

### Level D — leaderboard strategy title

A title is a **breadcrumb only**.

Never infer that a strategy called “Price Elasticity Breakout” uses our proposed elasticity formula. Never infer that “sharpe classifier” predicts Sharpe in a particular way. Use titles only to assess whether an idea class may already be crowded.

---

## 3. Official Q24 blockchain-data clue

Source:

- https://quantiacs.com/documentation/en/examples/q24_crypto_guide.html

The official Q24 crypto guide explicitly demonstrates:

```python
blockchain_metrics = qndata.blockchaincom_load_list()
miners_rev = qndata.blockchaincom_load_data(id="miners-revenue")
```

The same guide states that Q24 strategies could use only Quantiacs-provided data.

### Why this matters

Our current Q25 research stack is overwhelmingly built from:

- daily OHLCV;
- historical `is_liquid`;
- transforms of the cross-section derived from those objects.

A blockchain-network series is a **new information primitive**, not another transform of price.

That makes it potentially more valuable than another clever ranking rule over the same OHLCV inputs.

### Critical admissibility caveat

Do **not** interpret Q24 support as automatic Q25 approval.

Before a Q25 submission uses `blockchaincom_load_data`, the agent must confirm:

1. the loader works in the current Q25 environment;
2. the current Q25 official rules permit that Quantiacs-provided dataset;
3. the metric's timestamp/publication semantics are causal at the decision point;
4. multipass/replay receives the same historical data without hidden current-state leakage.

Until those are verified, classify on-chain research as:

> **research lead — Q25 admissibility unverified**

### The wrong way to use it

Do not say:

> miner revenue is high, therefore buy BTC.

That violates our asset-agnostic spirit and may create a hard-coded symbol dependency.

### The better formulation

Use a global network variable as a **state conditioner** for an automatic cross-sectional rule.

Examples:

- when miner-revenue growth is accelerating, does residual momentum become more/less persistent?
- when on-chain activity contracts while prices remain strong, do low-volatility or high-efficiency names outperform?
- does on-chain stress interact with **age since `is_liquid` entry**?
- do price/volume elasticity states behave differently during network expansion vs contraction?
- does on-chain state change the half-life of forecast surprise?

This gives the candidate at least two potential novelty axes:

- new information primitive;
- new timing/state interaction.

### Keep the first experiment tiny

Do **not** start with 40 blockchain metrics.

Start with:

- one metric;
- one causal transform;
- one interaction;
- one direction hypothesis;
- one direct falsifier.

An ideal first preregistration looks more like:

```text
Primitive: miner-revenue log growth / acceleration
Interaction: liquidity-transition age
Hypothesis: recently admitted assets are more fragile during deteriorating network state
Portfolio: long mature liquid assets; cash if no qualifying names
Falsifier: randomize network-state dates while preserving state frequency
```

rather than a giant ML feature soup.

---

## 4. On-chain hypothesis slate for ideation

These are **sketches**, not preregistered hypotheses. The next agent should generate its own 24-candidate slate and score them before running returns.

### A. Network stress × liquidity age

**Primitive:** on-chain growth/stress metric + days since `is_liquid` entry.

**Mechanism:** newer large-cap entrants may have less stable ownership/liquidity structure during network contraction.

**Nearest incumbent:** V11 lifecycle.

**Why potentially new:** V11 already uses liquidity lifecycle, but not necessarily a distinct network-state primitive.

**Falsifier:** substitute market realized volatility for the network state. If identical, the on-chain object adds nothing.

### B. On-chain / price disagreement

**Primitive:** standardized on-chain trend minus standardized market-price trend.

**Mechanism:** price rising while underlying network activity deteriorates may represent fragile repricing; the opposite may represent underreaction.

**Nearest incumbent:** trend/factor family.

**Falsifier:** replace on-chain leg with volume trend.

### C. On-chain state × self-elasticity

**Primitive:** network state and asset price displacement per unit abnormal dollar volume.

**Mechanism:** absorption/exhaustion may mean different things when network-level activity is expanding vs contracting.

**Nearest incumbent:** V12 and range-volume geometry.

**Falsifier:** remove interaction and keep only elasticity.

### D. Network acceleration × residual surprise

**Primitive:** change in on-chain state + online residual forecast error.

**Mechanism:** unexpected asset repricing may persist longer during improving network state and reverse faster during deterioration.

**Nearest incumbent:** none exact; touches V10 residuals.

**Falsifier:** use raw residual return instead of model surprise.

### E. On-chain state transition event

**Primitive:** causal crossing of a rolling on-chain percentile/state threshold.

**Mechanism:** transitions may matter more than level.

**Nearest incumbent:** regime conditioned.

**Falsifier:** matched-frequency random transition dates.

### F. Network-state persistence

**Primitive:** run length / age of network state rather than current level.

**Mechanism:** late-cycle state duration may change which cross-sectional characteristics survive.

**Nearest incumbent:** opportunity-density / regime.

**Falsifier:** current state only.

### G. Multi-metric agreement — only after single-metric tests

**Primitive:** agreement of at most 2–3 independently interpretable network metrics.

**Mechanism:** broad network confirmation may be more robust than one noisy metric.

**Falsifier:** one metric alone and shuffled metric pairing.

Do not implement G until at least one single-metric mechanism survives initial causality and fold testing.

---

## 5. Public predictive-coding clue

Source:

- https://github.com/RinKaname/project-001/blob/master/predictive_coding_quantiacs.py

The public code builds a stateful online predictive-coding network and updates its internal weights from prediction error.

We should **not copy this architecture**.

The interesting idea is simpler:

> A model's causal forecast error can itself be a market-state variable.

That is different from asking whether momentum is positive or whether residual return was high.

### Define surprise carefully

At decision time `t`:

```text
forecast made at t-1 for outcome t
surprise_t = realized_t - forecast_{t-1→t}
```

The model used to produce the forecast can be trivial.

Start with:

- rolling ridge;
- rolling OLS;
- EWMA conditional mean;
- tiny autoregression;
- simple residual-response model.

The model's complexity is **not** the research contribution.

The research contribution is whether:

- surprise persists;
- surprise reverses;
- surprise half-life changes by regime;
- cross-model disagreement predicts opportunity;
- calibration drift identifies state transitions.

### Statefulness warning

Any online model must survive:

- restart;
- multipass;
- prefix replay;
- truncated lookback windows;
- deterministic initialization.

A model that only works because a Python object remembers unrecorded prior state is not a valid research result.

Where practical, make the state reconstructable from the input history.

---

## 6. Online-surprise hypothesis slate

### A. Surprise persistence

Predict next-day market-residual return with a tiny rolling model.

Rank liquid assets by current prediction error.

Question:

> Do unexpectedly strong residual realizations continue more than equally strong raw residual returns?

**Nearest incumbent:** V10 residual momentum.

**Key ablation:** raw residual return rank.

### B. Surprise reversal

Same primitive, opposite economic thesis.

Large positive surprise may represent temporary overshoot.

The direction must be preregistered before looking at returns.

### C. Calibration-drift state

Measure rolling bias / absolute error of the model for each asset or the market.

Question:

> When the old model stops explaining returns, does the cross-section enter a different alpha regime?

This is more like a structural-break detector than a return forecast.

### D. Surprise half-life

Estimate whether yesterday's surprise is absorbed in 1, 3, 5, etc. days.

Avoid high-dimensional lag optimization. Test a coarse short/medium structure.

### E. Cross-model disagreement

Use 2–3 deliberately different tiny models.

Possible roles:

- high disagreement = uncertainty → hold cash;
- high disagreement = opportunity → concentrate only when one model has predeclared state reliability.

Do not test both directions and keep the winner under one experiment id.

### F. Forecast disagreement × liquidity age

New entrants may generate unusually unstable model predictions because their historical state is short or shifting.

This could be a cleaner extension of liquidity hysteresis than another return-based lifecycle score.

### G. Forecast-error topology

Build a residual/surprise correlation graph rather than a raw-return graph.

Question:

> Does topology of *what models are failing to explain* provide earlier regime information than return topology itself?

This could become a bridge between forecast-surprise and correlation-topology families.

---

## 7. Official rolling-ML reference

Source:

- https://github.com/quantiacs/strategy-ml-voting-crypto

Quantiacs maintains an official example demonstrating rolling model retraining with a voting classifier.

Use it for:

- understanding causal rolling retraining;
- backtester integration;
- model-state lifecycle;
- retraining cadence mechanics.

Do **not** use it as proof that voting classifiers are good Q25 alpha.

### Our ML rule

Machine learning should enter only after the mechanism is defined.

Bad:

> feed 70 indicators into XGBoost and maximize Sharpe.

Better:

> predict whether a predeclared residual-surprise state resolves by continuation or reversal using three causal inputs, then compare against the same rule without the classifier.

A model should compress a mechanism, not replace one.

---

## 8. Current Q25 leaderboard breadcrumbs

Source:

- https://quantiacs.com/leaderboard/25

At the time of the sweep, public titles included examples such as:

- `sharpe classifier`;
- `022_xgboost_rolling_classifier`;
- `Q25-19 v15 - Correlation Cluster EMA-RSI`;
- `Markov Upgrade`;
- `Price Elasticity Breakout by Rich`;
- `High-Low Range Continuity by Rich`;
- `Q25 LowVol90 Top1`;
- `Q25 ES Compression Breakout VT30`;
- `Q25 ES Breadth Dispersion VT30`.

### What an agent may infer

Only this:

- rolling/classifier ideas are being explored;
- low-volatility is being explored;
- cluster/correlation ideas are being explored;
- elasticity/range ideas are being explored;
- compression/breadth ideas are being explored.

### What an agent may NOT infer

Do not infer:

- exact features;
- formulas;
- thresholds;
- training labels;
- holding periods;
- portfolio construction;
- whether the title accurately describes the submitted code.

The current leaderboard can therefore help us **avoid crowded generic ideas**, but it cannot provide reproducible strategy details.

### Do not optimize against preview/OOS

Some displayed strategies have only a handful of days after submission.

An enormous preview/OOS Sharpe over a tiny sample is not evidence to chase.

Treat all current Q25 preview observations as contaminated diagnostics.

---

## 9. Price-volume elasticity / absorption geometry

A leaderboard title around “Price Elasticity Breakout” is only a breadcrumb, but the mechanism space itself is worth exploring because it fits our existing `range_volume_geometry` frontier while remaining structurally distinct from V12.

### Distinguish it from V12

V12 asks roughly:

> can abnormal volume in asset i predict next residual return in asset j through a directed network?

Elasticity research should ask something different:

> how much price/range displacement did this asset achieve per unit of abnormal flow, and what does that geometry imply about absorption, exhaustion, or fragile repricing?

No directed cross-asset network is required.

### Candidate primitives

Use robustly normalized versions of:

- absolute return / abnormal dollar volume;
- true range / abnormal dollar volume;
- close-location value × abnormal volume;
- directional displacement / intraday range;
- volume consumed per unit net displacement;
- path efficiency conditioned on volume shock;
- change in elasticity relative to asset history.

Avoid unstable literal division near zero. Prefer:

- logs;
- ranks;
- signed ranks;
- winsorized ratios;
- bounded transforms.

### Economic states worth distinguishing

#### High volume + low displacement

Possible interpretation:

- absorption;
- distribution;
- crowded two-sided trading;
- exhaustion.

#### Low/moderate volume + high displacement

Possible interpretation:

- thin repricing;
- information shock;
- fragile move;
- efficient directional discovery.

#### High range + close near extreme

Different from:

#### High range + close near midpoint

The interaction is the point.

### Falsifiers

- randomize the pairing between price displacement and volume while preserving each marginal rank;
- replace elasticity with abnormal volume alone;
- replace geometry with raw return magnitude;
- invert close-location interpretation;
- add one-day execution delay.

If the effect survives destroyed interactions, the elasticity story is probably false.

---

## 10. Benchmark-composition / index ecology lead

Public Q24 optimizer source:

- https://github.com/Thanh-Van-2001/quantiacs_tool

The public code references:

```python
qndata.index_load_weights(index_name="CRYPTO10")
```

This suggests a possible information object we have not exploited directly:

> the evolving composition and concentration of the Crypto10 benchmark itself.

### Why this could be different

`is_liquid` gives a binary membership state.

Historical benchmark weights, if available and admissible, may reveal more:

- concentration changes;
- member rank migration;
- relative market-cap acceleration;
- entrant pressure;
- incumbent decay;
- benchmark leadership turnover;
- concentration shocks.

### Potential features

- Herfindahl concentration / effective number of names;
- top-1 / top-3 weight concentration;
- weight change rank;
- acceleration of benchmark weight;
- entrant/re-entry weight trajectory;
- rank-crossing events;
- dispersion of benchmark weights;
- turnover of index leadership;
- age since entry × benchmark weight slope.

### Critical timing risk

If monthly index membership/weights are determined at month end for the next month, use only the version historically available at the decision date.

Do not let finalized month-end composition leak backward into earlier dates.

### Q25 admissibility

Treat this as **unverified for Q25** until confirmed.

If the loader is not permitted or behaves in a noncausal way under Q25 replay, abandon the external-data version and keep the concept as an `is_liquid`-only lifecycle/topology experiment.

---

## 11. Public persistent-low-volatility control

Source:

- https://github.com/berabhishek/quantiacs-q25-strategies

The public repo contains an unusually simple Q25 research rule:

1. calculate long-horizon realized volatility;
2. rank currently liquid assets;
3. equal-weight a low-volatility subset.

Its authors report that persistent low volatility was their strongest 2024–2025 local experiment.

Those numbers are **not ours** and are not official platform evidence.

### Why reproduce it anyway

It is a good control because:

- it is simple;
- turnover is naturally low;
- it is easy to audit;
- it helps tell us whether sophisticated candidates add value beyond a boring defensive selection rule.

### Classification

Do not call this a frontier discovery.

Label it:

> **external control / benchmark**

### Reproduction protocol

Reimplement from first principles rather than copy/paste.

Test:

- reasonable broad lookback plateaus, not exact published tuning;
- bottom-vol fraction plateaus;
- historical `is_liquid` correctness;
- standard cost ladder;
- full chronology;
- residual/correlation against C165, factor balance and other defensive sleeves.

If it works but is highly correlated with an incumbent, keep it as a diagnostic control.

---

## 12. Q24 winner: the low-turnover lesson

Source:

- https://quantiacs.com/leaderboard/24

The public Q24 leaderboard reports the winner `Q24_Tobin_crypto` with:

- contest Sharpe: **3.76**;
- max drawdown: **-17.06%**;
- average turnover: **0.78%**.

Do not infer the winner's hidden signal from these statistics.

The useful lesson is portfolio-level:

> a strong live contest result did not require frantic trading.

This reinforces our preference for mechanisms that are naturally:

- persistent;
- sparse;
- event-driven;
- slow to abandon positions;
- cash-tolerant;
- high expected information per unit turnover.

It also argues against assuming that more frequent adaptation is automatically more sophisticated.

---

## 13. Public Optuna Q24 optimizer: mostly an anti-pattern

Source:

- https://github.com/Thanh-Van-2001/quantiacs_tool

The code searches conventional families such as:

- SMA/EMA;
- RSI;
- MACD;
- breakout;
- inverse volatility;
- combined technical scores;

with Optuna maximizing in-sample Sharpe.

### What to learn from it

Useful:

- API patterns;
- CRYPTO10 benchmark loader clue;
- broad picture of what generic public participants may already be doing.

Not useful for our research process:

- full-history hyperparameter maximization;
- selecting the best TA family from many trials;
- treating optimized parameter points as independent evidence.

Our novelty contract exists specifically to avoid this mode of research.

---

## 14. New mechanism family: forecast surprise

Recommended catalog definition:

```text
Primitive:
    prediction error from a causal rolling model

Possible transforms:
    signed surprise
    standardized surprise
    surprise rank
    rolling calibration bias
    surprise half-life

State variables:
    liquidity age
    vol term structure
    market topology
    on-chain state (if admissible)

Portfolio roles:
    cross-sectional selector
    continuation/reversal alpha
    gross-risk gate
    cash trigger
```

### Main risk

This family can easily devolve into hidden feature mining.

The model must remain tiny enough that the agent can answer:

> what was forecast, why was that forecast reasonable, and why should the error matter economically?

---

## 15. New mechanism family: model disagreement

Recommended definition:

```text
Primitive:
    disagreement among 2–3 causal, deliberately different simple models

Do not use:
    50-model AutoML ensembles
    full-history model weighting
    target leakage through contemporaneous labels
```

Interesting questions:

- Does disagreement predict poor calibration and therefore justify cash?
- Does disagreement mark a regime transition where residual alpha broadens?
- Is one model's signal more reliable only when another disagrees?
- Does disagreement spike before correlation topology changes?

### Falsifier

Randomly swap model outputs across dates/assets while preserving each model's marginal score distribution.

---

## 16. New mechanism family: index ecology

Only pursue if the data path is Q25-admissible.

Recommended definition:

```text
Primitive:
    historical CRYPTO10 membership/weights as a dynamic market-cap state

Transforms:
    concentration
    rank migration
    entry age
    weight slope/acceleration
    leadership turnover

Portfolio use:
    cross-sectional selection
    maturity filter
    state-conditioned gross
```

Avoid turning the benchmark weights directly into a buy-and-hold benchmark clone.

The signal must exploit **change in ecology**, not simply hold the largest member.

---

## 17. First-pass implementation priorities

If the next agent has enough compute/data access, I would allocate the default 24 hypotheses as follows.

| Family | Idea count | Why |
|---|---:|---|
| On-chain state × cross-section | **7** | genuinely new primitive; highest conceptual novelty |
| Online surprise / disagreement | **7** | new transform/state object using admissible OHLCV if kept simple |
| Price-volume elasticity | **5** | strong economic story; OHLCV-only; distinct from V12 if designed carefully |
| Benchmark/index ecology | **5** | potentially very novel, but contingent on Q25 data permission |

If on-chain or index-weight data are not admissible, do **not** force them.

Reallocate those slots to:

- forecast surprise;
- vol term structure;
- correlation topology;
- range-volume geometry;
- liquidity hysteresis.

---

## 18. Suggested six preregistrations from that slate

Do not blindly use these exact six; they are a strong starting shape.

### 1. `onchain_liquidity_age_r1`

Global network-state deterioration × age since historical liquidity entry.

### 2. `onchain_elasticity_interaction_r1`

Network state × self-price/volume elasticity.

### 3. `residual_surprise_persistence_r1`

Tiny rolling residual-return model; test whether forecast surprise persists beyond raw residual momentum.

### 4. `forecast_disagreement_cashgate_r1`

Two or three simple models; high disagreement preregistered as a risk-off/cash state.

### 5. `range_volume_absorption_r1`

High abnormal volume + low displacement + close-location geometry as absorption/exhaustion state.

### 6. `crypto10_weight_migration_r1`

Historical benchmark-weight acceleration / rank migration, only if current admissibility/timing checks pass.

A sensible implementation budget would then choose the **three most novel/falsifiable** after preregistration and cheap L0/L1 checks.

---

## 19. Required pre-code questions for every external lead

Before writing strategy code, answer:

```text
Source URL:
What exactly did the source reveal?
What are we inferring vs actually observing?
Is the source official or third party?
Is any performance claim independently trusted?  NO by default.
What information primitive are we borrowing?
Is that primitive Q25-admissible?
What timestamp is actually available at decision time?
Nearest incumbent:
Novelty axes changed:
Why this is not just a renamed incumbent:
Primary falsifier:
Simplest implementation:
What would make us kill it before a backtest?
```

If the agent cannot distinguish observed source facts from its own inference, it is not ready to implement the idea.

---

## 20. External-data causality checklist

For blockchain or benchmark/index data, explicitly verify:

- historical timestamps;
- publication delay;
- revision behavior;
- whether a historical query returns revised values;
- whether the final day's value is known before portfolio generation;
- missing-data semantics;
- timezone/date alignment with crypto daily bars;
- availability in multipass windows;
- current contest permission;
- runtime impact.

When uncertain, apply a conservative lag and document it.

A small performance loss from conservative timing is preferable to an unprovable causality assumption.

---

## 21. ML causality checklist

For rolling models:

- every target used for training must already be realized;
- feature normalization must use historical-only statistics;
- model selection cannot inspect the live contest window;
- retraining cadence must be deterministic;
- random seeds must be frozen;
- multipass and restart output must match;
- the model must handle changing `is_liquid` membership without asset-specific hard coding;
- the label definition must be fixed before return inspection;
- compare against a non-ML ablation.

If the ML model only wins because of a large hyperparameter sweep, classify it as fragile until disproven.

---

## 22. What not to waste time on from the public sweep

Deprioritize as independent-alpha research:

- another SMA crossover;
- another RSI filter;
- another MACD variant;
- another Donchian lookback;
- generic cross-sectional momentum;
- generic inverse volatility;
- generic HRP without a topology mechanism;
- generic Markov/HMM regime selection without a new observable;
- generic XGBoost over a large TA feature zoo;
- “classifier” work with no clear label economics;
- full-history Optuna Sharpe maximization.

These may still be useful **controls**.

---

## 23. Crowding implications from public titles

The public leaderboard suggests some idea classes are visibly popular.

That should raise the novelty bar for:

- generic classifier strategies;
- low-volatility selection;
- correlation clustering;
- EMA/RSI cluster hybrids;
- Markov regime models;
- simple compression breakout;
- simple range continuity;
- generic price elasticity.

Our response should not be “avoid them completely.”

Our response should be:

> require a more precise mechanism and at least two changed novelty axes.

Examples:

- not “classifier,” but **forecast-calibration drift as regime state**;
- not “correlation cluster,” but **surprise-topology bridge-node migration**;
- not “low vol,” but **volatility term-structure curvature conditional on liquidity age**;
- not “elasticity breakout,” but **signed absorption geometry conditional on close location and historical elasticity state**.

---

## 24. Portfolio-level lessons from the sweep

Three useful principles emerge even if none of the public alphas reproduce.

### 1. Low turnover deserves explicit preference

Q24's winning public profile reinforces the value of persistent holdings.

Whenever two mechanisms have similar evidence, prefer the one that generates less unnecessary position movement.

### 2. The next edge may be in a new primitive, not a new transform

Blockchain state and benchmark composition are more structurally novel than a 17th technical indicator.

### 3. Forecast uncertainty can be an alpha-state variable

Even if predicting returns directly is difficult, **when the model is wrong** or **when models disagree** may be useful information about market structure.

---

## 25. Research contamination warning

This memo itself creates contamination.

The agent now knows:

- a public low-vol strategy reportedly did well in 2024–2025;
- Q24 winner turnover was very low;
- current Q25 titles include classifiers, elasticity and range/correlation themes.

Therefore:

- do not call 2024–2025 a pristine validation period for hypotheses inspired by this memo;
- do not tune a candidate to reproduce public leaderboard behavior;
- document this memo as an idea source in each relevant preregistration;
- keep the live 2026-10-01 → 2027-01-31 contest window untouched.

---

## 26. Agent start command after reading this memo

After the normal mandatory reading sequence:

1. read `configs/external_research_leads.yaml`;
2. separate **Q25-admissible-now** from **needs-verification** primitives;
3. write a fresh 24-hypothesis slate across at least four mechanism families;
4. mark the public source/inspiration for any internet-derived idea;
5. score novelty/falsifiability **before returns**;
6. preregister at most six;
7. implement at most three;
8. reproduce external controls independently;
9. run the full testing pyramid;
10. compare residual value against incumbents;
11. record both positive and negative results so we never have to rediscover the same dead ends.

---

## 27. Source index

### Official Quantiacs

- Q25 leaderboard: https://quantiacs.com/leaderboard/25
- Q24 leaderboard: https://quantiacs.com/leaderboard/24
- Q24 crypto guide: https://quantiacs.com/documentation/en/examples/q24_crypto_guide.html
- Q25 contest page: https://quantiacs.com/contest
- Quantiacs crypto data docs: https://quantiacs.com/documentation/en/data/crypto.html
- Official rolling voting-classifier example: https://github.com/quantiacs/strategy-ml-voting-crypto

### Third-party public repositories

- Q25 low-vol / momentum research: https://github.com/berabhishek/quantiacs-q25-strategies
- Predictive-coding Quantiacs experiment: https://github.com/RinKaname/project-001/blob/master/predictive_coding_quantiacs.py
- Q24 Optuna / alpha factory: https://github.com/Thanh-Van-2001/quantiacs_tool

---

## Final instruction

The internet sweep is useful only if it **expands our hypothesis space without lowering our evidence standards**.

The next agent should be more adventurous about information primitives and more conservative about performance claims.

**Interesting source ≠ alpha. Interesting title ≠ implementation. Public Sharpe ≠ evidence. A new causal object that survives our own falsification process is the goal.**
