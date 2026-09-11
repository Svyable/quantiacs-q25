#!/usr/bin/env python3
"""Create Frontier-G preregistrations before any G returns are observed."""
from __future__ import annotations
import csv
import json
from pathlib import Path
from research.preregister import write_preregistration, sha256_file

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = "frontier_20260911g"
CREATED = "2026-09-11T12:00:00+00:00"
SCORE_BASIS = (
    "Research judgment after A–F; no Frontier-G returns. "
    "Does not reuse failed signed-triangle, weekly-posterior, or expert-policy formulas."
)

SLATE = [
    ("edge_uncertainty", "graph_uncertainty",
     "Rising variance of residual-correlation edges plus a positive own residual identifies idiosyncratic leadership during graph fragmentation.",
     "rotate uncertainty-change across currently eligible identities",
     dict(novelty=2, causal_clarity=2, falsifiability=2, parameter_economy=2, cost_plausibility=2, portfolio_complement=1)),
    ("spectral_gap_change", "graph_uncertainty",
     "A widening gap between the leading residual-correlation eigenvalues indicates collapsing independent opportunity.",
     "destroy the eigenvalue ordering",
     dict(novelty=2, causal_clarity=2, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("neighborhood_churn", "graph_uncertainty",
     "Turnover in an asset's strongest residual neighbors is a fragmentation state, not a static low-correlation sort.",
     "freeze neighbor identities",
     dict(novelty=2, causal_clarity=2, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("bridge_entropy", "graph_uncertainty",
     "High entropy of residual-edge weights identifies assets that are not concentrated in one correlated clique.",
     "degree-matched random edges",
     dict(novelty=2, causal_clarity=1, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("local_clustering_drift", "graph_uncertainty",
     "A falling residual clustering coefficient with positive residual trend marks escape from a crowded cohort.",
     "current clustering level only",
     dict(novelty=2, causal_clarity=2, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("signed_weight_dispersion", "graph_uncertainty",
     "Dispersion of signed residual-edge weights is a different object from triangle balance or centrality.",
     "absolute weights only",
     dict(novelty=2, causal_clarity=1, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("forecast_agreement", "forecast_structure",
     "Agreement between a slow residual-mean forecast and a fully realized one-week residual forecast identifies usable positive leadership.",
     "prefer disagreement while keeping the same slow-positive gate",
     dict(novelty=2, causal_clarity=2, falsifiability=2, parameter_economy=2, cost_plausibility=2, portfolio_complement=1)),
    ("leader_response_lag", "forecast_structure",
     "Shortening lag of an asset's residual response to the equal-liquid market identifies faster assimilation than a static delay sort.",
     "shuffle response lags inside the eligible cohort",
     dict(novelty=2, causal_clarity=2, falsifiability=2, parameter_economy=2, cost_plausibility=1, portfolio_complement=1)),
    ("two_speed_sign_lock", "forecast_structure",
     "Same-sign slow and fast residual forecasts are a weaker agreement object than rank agreement.",
     "require opposite signs",
     dict(novelty=1, causal_clarity=2, falsifiability=2, parameter_economy=2, cost_plausibility=1, portfolio_complement=1)),
    ("surprise_half_life", "forecast_structure",
     "Slow decay of residual AR forecast errors identifies incomplete assimilation rather than raw residual momentum.",
     "destroy lag order",
     dict(novelty=2, causal_clarity=2, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("interval_width_cash", "forecast_structure",
     "A widening residual prediction interval is a cash state, not a return forecast.",
     "constant interval width",
     dict(novelty=2, causal_clarity=2, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("calibration_slope", "forecast_structure",
     "The slope of predicted versus fully realized residual quantiles detects miscalibrated leadership.",
     "pooled residual quantile only",
     dict(novelty=2, causal_clarity=1, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("cost_relative_persistence", "execution_density",
     "Persistent residual leadership scaled by own relative ATR is more deployable than raw residual leadership.",
     "pair each asset with another eligible name's relative ATR",
     dict(novelty=2, causal_clarity=2, falsifiability=2, parameter_economy=2, cost_plausibility=2, portfolio_complement=1)),
    ("rank_stability_density", "execution_density",
     "Stable residual ranks plus positive residual trend identify when the cross-section contains tradable opportunity.",
     "current residual magnitude only",
     dict(novelty=2, causal_clarity=2, falsifiability=2, parameter_economy=2, cost_plausibility=1, portfolio_complement=1)),
    ("trade_distance_hurdle", "execution_density",
     "Only accept a new Monday book when the score improvement exceeds a predeclared ATR-linked distance.",
     "always accept the new book",
     dict(novelty=1, causal_clarity=2, falsifiability=2, parameter_economy=2, cost_plausibility=2, portfolio_complement=1)),
    ("no_trade_band", "execution_density",
     "A symmetric no-trade band around the current target reduces churn without post-hoc smoothing.",
     "zero band",
     dict(novelty=1, causal_clarity=2, falsifiability=2, parameter_economy=2, cost_plausibility=2, portfolio_complement=0)),
    ("delay_option", "execution_density",
     "Waiting one extra Monday has option value when residual persistence is below a fixed hurdle.",
     "never wait",
     dict(novelty=2, causal_clarity=2, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("monday_gap_cost", "execution_density",
     "Weekend range relative to Friday ATR is an execution-state, not a direction forecast.",
     "weekday range control",
     dict(novelty=2, causal_clarity=1, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("score_dispersion_cash", "opportunity_state",
     "Low cross-sectional residual-score dispersion is a cash state because opportunity is concentrated.",
     "mean residual instead of dispersion",
     dict(novelty=2, causal_clarity=2, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("breadth_of_positive_residual", "opportunity_state",
     "The fraction of eligible names with positive residual trend is an opportunity-density gate.",
     "equal-liquid market sign only",
     dict(novelty=1, causal_clarity=2, falsifiability=2, parameter_economy=2, cost_plausibility=1, portfolio_complement=1)),
    ("disagreement_across_horizons", "opportunity_state",
     "Disagreement among 7/21/63-day residual ranks is a cash state rather than a blend weight.",
     "replace disagreement with residual variance",
     dict(novelty=2, causal_clarity=2, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("concentration_penalty", "opportunity_state",
     "Penalize names whose residual score share exceeds a predeclared concentration cap.",
     "no concentration penalty",
     dict(novelty=1, causal_clarity=2, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("liquidity_age_conditioner", "opportunity_state",
     "Use age-since-liquidity-entry only as a conditioner on another score, not as standalone alpha.",
     "current is_liquid only",
     dict(novelty=1, causal_clarity=2, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("failed_recovery_count", "opportunity_state",
     "Repeated failed recoveries after a defined residual shock identify exhaustion rather than dip-buying.",
     "shock depth alone",
     dict(novelty=2, causal_clarity=2, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
]

DESIGNS = {
    "edge_uncertainty": dict(
        incumbent="Frontier-B topology migration / Frontier-F signed-triangle change",
        axes=["information_primitive", "transform", "timing_or_state_condition"],
        window=63, grid=[42, 63, 84],
        thesis=SLATE[0][2], falsifier=SLATE[0][3],
        transform=(
            "Each Monday t, among assets liquid at t and t-21 with finite residual history, "
            "form residual log returns (own minus equal-liquid market). Compute the W-day residual "
            "correlation matrix on [t-W+1, t] and the matched matrix ending t-21, requiring at least "
            "max(16, W//2) pairwise observations. Edge uncertainty is the standard deviation of "
            "off-diagonal correlations for that asset. Base score = clip((current-previous)/2, 0, 1) "
            "only if the asset's 21-day residual sum is positive. Ablation uses current uncertainty "
            "level mapped by clip(u,0,1) with the same residual-trend gate and warmup. Falsifier "
            "rotates the uncertainty-change vector inside the eligible finite cohort before clipping. "
            "No extra market-timing gate."
        ),
        ablation="current residual-edge uncertainty level without 21-day change",
        failure_mode="uncertainty change is a noisy rewrite of topology migration or residual trend",
    ),
    "forecast_agreement": dict(
        incumbent="Frontier-A AR forecast surprise / Frontier-F weekly payoff posterior",
        axes=["information_primitive", "transform", "timing_or_state_condition"],
        window=42, grid=[21, 42, 63],
        thesis=SLATE[6][2], falsifier=SLATE[6][3],
        transform=(
            "Residual = own log return minus equal-liquid market. Slow forecast = W-day residual mean. "
            "Fast forecast = fully realized 7-day residual mean. Both use completed bars only. Among "
            "currently liquid names with finite slow and fast forecasts, rank each forecast descending "
            "with first-method ties on sorted labels. Agreement = 1 - |rank_slow-rank_fast|/(n-1) when "
            "n>1. Base score = agreement when slow>0 and fast>0, else 0. Ablation ignores the fast "
            "forecast and agreement, scoring clip(slow,0,1) after dividing by the day's max positive "
            "slow (or 0 if none). Falsifier keeps the slow>0 and fast>0 gate but scores disagreement "
            "instead of agreement. No added market-timing gate."
        ),
        ablation="slow residual mean only; drop fast forecast and rank agreement",
        failure_mode="agreement collapses into residual momentum or the weekly posterior's pooled control",
    ),
    "cost_relative_persistence": dict(
        incumbent="V10 residual momentum / unimplemented Frontier-D/E execution hurdle",
        axes=["information_primitive", "transform", "timing_or_state_condition"],
        window=63, grid=[42, 63, 84],
        thesis=SLATE[12][2], falsifier=SLATE[12][3],
        transform=(
            "Residual = own log return minus equal-liquid market. Persistence = W-day rolling "
            "correlation between residual and residual lagged 7 days, floored at 0. Expected edge = "
            "W-day residual sum times persistence. Relative ATR = 14-day mean true range / close, "
            "true range using prior close. Base score = expected / (expected + relative ATR) when "
            "expected>0, else 0. Ablation drops ATR and uses clip(expected,0,1). Falsifier preserves "
            "expected edge but replaces own relative ATR with a rotated eligible identity's relative "
            "ATR before the same density map. ATR lookback 14 and lag 7 are fixed. No extra market-timing gate."
        ),
        ablation="persistent residual edge without dividing by own relative ATR",
        failure_mode="ATR scaling is inverse-vol in disguise or persistence adds no residual value",
    ),
    "spectral_gap_change": dict(
        incumbent="Frontier-B topology migration",
        axes=["information_primitive", "transform"],
        window=63, grid=[42, 63, 84],
        thesis=SLATE[1][2], falsifier=SLATE[1][3],
        transform="Change in (lambda1-lambda2)/sum(lambda) of the eligible residual-correlation matrix.",
        ablation="leading eigenvalue share only",
        failure_mode="spectral gap restates correlation concentration already tested in topology work",
        implemented=False,
    ),
    "leader_response_lag": dict(
        incumbent="Frontier-C assimilation acceleration",
        axes=["information_primitive", "transform", "timing_or_state_condition"],
        window=63, grid=[42, 63, 84],
        thesis=SLATE[7][2], falsifier=SLATE[7][3],
        transform="Median lag 0-5 of residual correlation with the equal-liquid market; falling lag is the score.",
        ablation="contemporaneous market beta only",
        failure_mode="lag compression duplicates rejected delay candidates",
        implemented=False,
    ),
    "rank_stability_density": dict(
        incumbent="opportunity-density / residual dispersion switch",
        axes=["information_primitive", "timing_or_state_condition"],
        window=63, grid=[42, 63, 84],
        thesis=SLATE[13][2], falsifier=SLATE[13][3],
        transform="Rolling Spearman stability of residual ranks, gated on positive residual trend.",
        ablation="residual magnitude without rank stability",
        failure_mode="stability is a volatility proxy or a restatement of residual dispersion",
        implemented=False,
    ),
}
IMPLEMENTED = ("edge_uncertainty", "forecast_agreement", "cost_relative_persistence")


def base_payload(name, design, digest_path=None):
    implemented = name in IMPLEMENTED
    path = f"strategies/generated/{CAMPAIGN}_{name}.py" if implemented else None
    return dict(
        experiment_id=f"{CAMPAIGN}_{name}",
        created_utc=CREATED,
        track="robustness",
        mechanism=name,
        thesis=design["thesis"],
        falsifier=design["falsifier"],
        nearest_incumbent=design["incumbent"],
        novelty_axes_changed=design["axes"],
        classification="discovery_hypothesis",
        primitive="Historical Quantiacs cryptodaily OHLCV and is_liquid; no external strategy data",
        data_admissibility="OHLCV_ONLY",
        timing="Completed daily bars only; toolbox applies candidate execution lag.",
        transform=design["transform"],
        selection="Positive bounded score top-K with label tie-breaking on sorted asset ids.",
        allocation="min(0.25, 1/K) times bounded score per selected name; no gross renormalization.",
        cash_rule="Missing model state or nonpositive score means cash.",
        rebalance="Monday entries; six-bar bounded carry; eligibility-loss exits stay closed until next Monday.",
        universe="historical is_liquid == 1 and positive finite close; rotations ignore inactive and future-listed assets",
        initial_free_parameters=["window", "top_k"],
        params={"window": design["window"], "top_k": 5},
        grid={"window": design["grid"]},
        fixed_constants={
            "atr_days": 14,
            "cost_lookback_is_atr": True,
            "fast_forecast_days": 7,
            "graph_lag": 21,
            "persistence_lag": 7,
            "residual_trend_days": 21,
        },
        folds_allowed_for_selection=["research", "dev"],
        validation="2023-2024 only after freeze; never drives mutation",
        selection_objective="minimum research/dev SR at 4/8/12% ATR costs with existing tie breakers",
        stop_rule="Existing central-parent destructive-control/ablation and 1.0 weak-alpha floor; no parameter expansion after returns; no automatic promotion.",
        ablation=design["ablation"],
        failure_mode=design["failure_mode"],
        cost_hypothesis="Weekly entries, cash, and name caps; exact ATR-linked costs decide viability.",
        portfolio_role="Research satellite requiring residual evidence versus generic controls and later incumbents",
        source_urls=[],
        source_notes="Original designs from the repository frontier map after A–F freezes. Unverified on-chain and index-data proposals excluded.",
        contamination_notes="A–F research/dev history repeatedly observed. No fresh holdout claim; no live data.",
        promotion_gates="configs/promotion_gates.yaml",
        code_path=path,
        status="IMPLEMENTED_PENDING_EVIDENCE" if implemented else "PREREGISTERED_NOT_IMPLEMENTED",
    )


def create():
    dest = ROOT / "experiments" / CAMPAIGN
    dest.mkdir(parents=True, exist_ok=False)
    slate = []
    for name, area, thesis, falsifier, scores in SLATE:
        slate.append(dict(
            id=name, area=area, thesis=thesis, falsifier=falsifier, scores=scores,
            priority_score=sum(scores.values()),
            performance_seen_before_score=False,
            score_basis=SCORE_BASIS,
            admissibility="OHLCV_ONLY",
        ))
    (dest / "idea_slate.json").write_text(json.dumps(slate, indent=2) + "\n")
    ledger = []
    hashes = {}
    for name, design in DESIGNS.items():
        payload = base_payload(name, design)
        _, digest = write_preregistration(dest / name, payload)
        hashes[name] = digest
        ledger.append([payload["experiment_id"], digest, "discovery_hypothesis", payload["status"]])
    candidates = []
    for name in IMPLEMENTED:
        design = DESIGNS[name]
        path = f"strategies/generated/{CAMPAIGN}_{name}.py"
        digest = hashes[name]
        for w in design["grid"]:
            candidates.append(dict(
                id=f"{name}_w{w}", family=name, mode="base",
                params={"window": w, "top_k": 5}, path=path,
                parent_id=None if w == design["window"] else f"{name}_w{design['window']}",
                preregistration=f"experiments/{CAMPAIGN}/{name}/preregistration.json",
                preregistration_sha256=digest,
            ))
        for mode in ("ablation", "falsifier"):
            candidates.append(dict(
                id=f"{name}_{mode}", family=name, mode=mode,
                params={"window": design["window"], "top_k": 5}, path=path,
                parent_id=f"{name}_w{design['window']}",
                preregistration=f"experiments/{CAMPAIGN}/{name}/preregistration.json",
                preregistration_sha256=digest,
            ))
    with (dest / "formula_ledger.csv").open("w") as f:
        writer = csv.writer(f)
        writer.writerow(["experiment_id", "preregistration_sha256", "classification", "status"])
        writer.writerows(ledger)
    manifest = dict(
        campaign=CAMPAIGN,
        candidates=candidates,
        controls=["equal_liquid", "inverse_vol_trend", "persistent_low_vol"],
        selection_folds=["research", "dev"],
        max_unique_candidates=15,
        automatic_promotion=False,
        protected_live_start="2026-10-01",
        classification_note="Three discovery hypotheses: residual-edge uncertainty change, two-speed forecast agreement, and cost-relative residual persistence.",
    )
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    plan = dict(
        campaign=CAMPAIGN,
        frozen_before_new_returns=True,
        secondary_diagnostics=dict(block_days=21, bootstrap_replicates=2000, seed=20260913),
        progression=(
            "Require all valid cells, central base beating both controls, >=2 base robust Sharpes >=1 "
            "and positive central dev residual SR. Only then test one extra execution day with SAME frozen "
            "parameters. Only survivors may receive a separately labeled contaminated 2023-2024 diagnostic; "
            "no 2025+ or live retrieval."
        ),
        policy_note="This progression rule allocates research compute; it does not replace repository promotion gates.",
        multiple_testing="24 sketches, six registrations, 15 new cells and three generic controls; A–F history already observed.",
    )
    (dest / "analysis_plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    (dest / "hashes.json").write_text(json.dumps(hashes, indent=2) + "\n")
    return dest, hashes


if __name__ == "__main__":
    dest, hashes = create()
    print(dest)
    for k, v in hashes.items():
        print(k, v)
