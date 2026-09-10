"""Preregister a finite, diverse frontier campaign before observing returns."""
from __future__ import annotations
import csv
import json
from pathlib import Path
from research.preregister import write_preregistration, sha256_file

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = "frontier_20260910"
# Names are economic hypotheses, not optimized parameter variants.
SLATE = {
    "forecast": [
        ("forecast_surprise", "Positive rolling AR residual forecast errors persist", "replace forecasts with other assets' forecasts", 11),
        ("surprise_reversal", "Large positive forecast errors reverse after overshoot", "raw residual instead of model surprise", 8),
        ("calibration_drift", "Rising signed model bias identifies structural repricing", "freeze model bias state", 9),
        ("error_half_life", "Slow decay of errors identifies incomplete assimilation", "destroy lag order", 8),
        ("model_disagreement", "Disagreement between AR and mean forecasts warrants cash", "replace disagreement with return dispersion", 10),
        ("error_topology", "Forecast error graph fragmentation precedes repricing", "use raw-return graph", 7),
    ],
    "geometry": [
        ("flow_absorption", "High flow with low body displacement and high close location indicates absorption", "permute current flow across assets", 11),
        ("failed_displacement", "Large range without follow-through signals exhaustion", "remove close location", 8),
        ("elasticity_acceleration", "Rising displacement per unit flow indicates fragile repricing", "remove flow pairing", 9),
        ("range_compression", "Volume-supported shrinking ranges precede continuation", "range alone", 8),
        ("downside_absorption", "High-flow lower wicks damp subsequent downside", "invert close location", 7),
        ("gap_repair", "Partial overnight gap repair reveals directional absorption", "replace gaps with close returns", 7),
    ],
    "volatility": [
        ("vol_curve", "Concave descending vol curves with positive recovery returns identify stabilization", "invert shape gate", 11),
        ("vol_of_vol", "Falling variance instability precedes safer deployment", "realized volatility level only", 8),
        ("semivariance_curve", "Downside variance decays faster than upside variance", "symmetric variance", 9),
        ("tail_recovery", "Shortening underwater duration indicates improving recovery", "drawdown depth alone", 8),
        ("range_return_wedge", "Range variance and close variance disagreement identifies choppy markets", "close variance alone", 7),
        ("vol_spillover", "Changes in lagged variance transmission reveal fragile leaders", "destroy lead-lag structure", 7),
    ],
    "membership_topology": [
        ("reentry_hysteresis", "Repeat top10 entrants require longer stabilization than first entrants", "erase prior membership spells", 10),
        ("cohort_maturity", "Broad entrant maturity changes cross-sectional risk appetite", "current membership alone", 8),
        ("leadership_churn", "Rapid turnover of return leadership warrants cash", "current rank dispersion only", 8),
        ("bridge_migration", "Changing residual graph bridges identify integration shocks", "static low correlation", 9),
        ("cluster_reconnection", "Reconnecting isolated return clusters predicts assimilation", "freeze graph", 7),
        ("rank_hysteresis", "Persistent ranking after membership loss differs from first entry", "erase membership history", 7),
    ],
}
DESIGNS = {
    "forecast_surprise": ("V10 residual momentum", ["transform", "timing_or_state_condition"], 42),
    "flow_absorption": ("V12 directed volume diffusion", ["transform", "timing_or_state_condition"], 42),
    "vol_curve": ("C165 / inverse-vol trend", ["transform", "timing_or_state_condition"], 21),
    "model_disagreement": ("residual dispersion switch", ["information_primitive", "timing_or_state_condition"], 42),
    "reentry_hysteresis": ("V11 simple entry lifecycle", ["transform", "timing_or_state_condition"], 42),
    "bridge_migration": ("CoCrash126", ["transform", "timing_or_state_condition"], 42),
}
IMPLEMENTED = ("forecast_surprise", "flow_absorption", "vol_curve")


def create_campaign(root=ROOT):
    directory = root / "experiments" / CAMPAIGN
    # Immutable creation: reruns never rewrite the original research contract.
    directory.mkdir(parents=True, exist_ok=False)
    slate = []
    for area, hypotheses in SLATE.items():
        for name, thesis, falsifier, score in hypotheses:
            # Six 0–2 axes; lower scores explicitly sacrifice cost/complement/clarity.
            axes = [2, 2, 2, 2, 2, 2]
            for i in [4, 5, 1, 0, 3]:
                if sum(axes) > score:
                    axes[i] -= min(2, sum(axes) - score)
            slate.append(dict(id=name, area=area, thesis=thesis, falsifier=falsifier,
                              scores=dict(zip(["novelty", "causal_clarity", "falsifiability", "parameter_economy", "cost_plausibility", "portfolio_complement"], axes)),
                              priority_score=score, score_basis="research judgment before returns"))
    (directory / "idea_slate.json").write_text(json.dumps(slate, indent=2) + "\n")
    template = (root / "templates/frontier_strategy.py.tpl").read_text()
    candidates = []
    ledger = []
    for name, (incumbent, axes, window) in DESIGNS.items():
        idea = next(s for s in slate if s["id"] == name)
        params = dict(window=window, persistence=5, top_k=5)
        grid = [window * 2 // 3, window, window * 4 // 3]
        path = f"strategies/generated/{CAMPAIGN}_{name}.py"
        payload = dict(experiment_id=f"{CAMPAIGN}_{name}", track="robustness",
            mechanism=name, thesis=idea["thesis"], falsifier=idea["falsifier"],
            nearest_incumbent=incumbent, novelty_axes_changed=axes,
            primitive="Quantiacs daily OHLCV and historical is_liquid only",
            data_admissibility="VERIFIED_OHLCV_AGAINST_SUPPLIED_Q25_RULES",
            timing="completed daily bars; forecast coefficients strictly pre-outcome",
            selection="positive scores, top-K, deterministic label tie breaks",
            allocation="fixed slots min(0.25, 1/K); unused slots cash",
            rebalance="Mondays; immediate liquidity loss exits",
            universe="historical is_liquid == 1; no hand-picked symbols",
            cash_rule="no positive score means cash", params=params,
            grid={"window": grid}, folds_allowed_for_selection=["research", "dev"],
            validation="2023-2024 only after freeze; never drives mutation",
            selection_objective="minimum research/dev Sharpe across 0.04/0.08/0.12 ATR cost; then worst DD, lower turnover, id",
            stop_rule="freeze if falsifier or ablation matches/beats base development score; no automatic promotion",
            ablation={"forecast_surprise":"raw residual", "flow_absorption":"abnormal flow alone", "vol_curve":"inverse long volatility"}.get(name, "remove interaction"),
            failure_mode="state proxy duplicates incumbent or decays before next execution",
            cost_hypothesis="weekly rebalancing limits unnecessary target changes",
            portfolio_role="orthogonal satellite only if matched residual tests support it",
            source_urls=["https://quantiacs.com/documentation/en/examples/q24_crypto_guide.html"],
            source_notes="Mechanism inspired by repository frontier and supplied Q25 example; Lattice motivates finite candidate elimination only, not financial evidence",
            contamination_notes="2016-2022 reused development; 2025+ previously viewed diagnostics; live excluded",
            promotion_gates="configs/promotion_gates.yaml", code_path=path if name in IMPLEMENTED else None,
            template_sha256=sha256_file(root / "templates/frontier_strategy.py.tpl"),
            status="IMPLEMENTED_PENDING_EVIDENCE" if name in IMPLEMENTED else "PREREGISTERED_NOT_IMPLEMENTED")
        _, digest = write_preregistration(directory / name, payload)
        ledger.append([payload["experiment_id"], digest, name, "PENDING", ""])
        if name not in IMPLEMENTED:
            continue
        replacements = dict(ID=payload["experiment_id"], EXPERIMENT=payload["experiment_id"], HASH=digest,
                            THESIS=idea["thesis"], INCUMBENT=incumbent, AXES=", ".join(axes), FAMILY=name, PARAMS=repr(params))
        source = template
        for k, v in replacements.items():
            source = source.replace(f"__{k}__", v)
        (root / path).write_text(source)
        for w in grid:
            candidates.append(dict(id=f"{name}_w{w}", family=name, path=path,
                params=dict(params, window=w), mode="base", parent_id=None if w == window else f"{name}_w{window}",
                preregistration=f"experiments/{CAMPAIGN}/{name}/preregistration.json", preregistration_sha256=digest))
        for mode in ["ablation", "falsifier"]:
            candidates.append(dict(id=f"{name}_{mode}", family=name, path=path, params=params,
                mode=mode, parent_id=f"{name}_w{window}",
                preregistration=f"experiments/{CAMPAIGN}/{name}/preregistration.json", preregistration_sha256=digest))
    with (directory / "formula_ledger.csv").open("w") as f:
        writer = csv.writer(f)
        writer.writerow(["experiment_id", "preregistration_sha256", "mechanism", "status", "observed_metrics"])
        writer.writerows(ledger)
    manifest = dict(campaign=CAMPAIGN, candidates=candidates,
        controls=["equal_liquid", "inverse_vol_trend", "persistent_low_vol"],
        protected_live_start="2026-10-01", selection_folds=["research", "dev"],
        max_unique_candidates=len(candidates), automatic_promotion=False)
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return directory


if __name__ == "__main__":
    print(create_campaign())
