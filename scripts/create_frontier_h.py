#!/usr/bin/env python3
"""Create Frontier-H preregistrations before any H returns are observed."""
from __future__ import annotations
import csv
import json
from pathlib import Path
from research.preregister import write_preregistration

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = "frontier_20260911h"
CREATED = "2026-09-11T12:30:00+00:00"
SCORE_BASIS = (
    "Research judgment after A–F; topology_migration is the only new-campaign "
    "family with a valid development floor. No Frontier-H returns. Does not "
    "reuse failed A–F formulas, unsigned centrality migration, or uncommitted G objects."
)

SLATE = [
    ("clustering_escape", "local_graph_structure",
     "A falling residual-correlation clustering coefficient during graph fragmentation, with positive residual trend, marks escape from a crowded clique rather than a static low-centrality sort.",
     "rotate clustering-change across currently eligible identities",
     dict(novelty=2, causal_clarity=2, falsifiability=2, parameter_economy=2, cost_plausibility=2, portfolio_complement=2)),
    ("wedge_closure", "local_graph_structure",
     "The residual of local clustering versus degree centrality identifies bridges leaving cliques.",
     "degree-matched clustering",
     dict(novelty=2, causal_clarity=1, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("triangle_count_drift", "local_graph_structure",
     "A falling count of strong residual triangles is a different object from signed triangle balance.",
     "current triangle count only",
     dict(novelty=1, causal_clarity=2, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("strength_entropy", "local_graph_structure",
     "Rising entropy of an asset's residual-edge weights identifies leaving a concentrated clique.",
     "degree-matched random edges",
     dict(novelty=2, causal_clarity=1, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("kcore_exit", "local_graph_structure",
     "Leaving a high residual k-core during fragmentation is clique-exit, not low beta.",
     "current k-core level",
     dict(novelty=2, causal_clarity=1, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("motif_rotation", "local_graph_structure",
     "Replacement of an asset's dominant 3-node residual motif is a local-structure change.",
     "freeze motif labels",
     dict(novelty=2, causal_clarity=1, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("factor_loading_escape", "spectral_factor_topology",
     "A declining absolute loading on the leading residual-correlation eigenvector during spectral-gap compression identifies leaving the common residual factor.",
     "rotate loading-change across currently eligible identities",
     dict(novelty=2, causal_clarity=2, falsifiability=2, parameter_economy=2, cost_plausibility=2, portfolio_complement=2)),
    ("spectral_gap_cash", "spectral_factor_topology",
     "A widening leading-eigenvalue gap is a cash state because independent residual opportunity is collapsing.",
     "invert the gap-change gate",
     dict(novelty=2, causal_clarity=2, falsifiability=2, parameter_economy=2, cost_plausibility=1, portfolio_complement=1)),
    ("subspace_drift", "spectral_factor_topology",
     "The principal-angle change of the top-two residual eigenspace is factor rotation, not centrality.",
     "random orthogonal rotation of the same subspace",
     dict(novelty=2, causal_clarity=2, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("participation_ratio", "spectral_factor_topology",
     "A falling inverse-participation-ratio of the leading residual eigenvector marks concentrating factor risk.",
     "leading eigenvalue share only",
     dict(novelty=2, causal_clarity=2, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("sign_unstable_factor", "spectral_factor_topology",
     "Names whose residual factor-loading sign flips while magnitude stays large are unstable leaders.",
     "magnitude without sign flips",
     dict(novelty=1, causal_clarity=1, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("residual_pca_momentum", "spectral_factor_topology",
     "Residual return orthogonal to the current leading eigenvector is a spectral residual, not a market residual.",
     "equal-liquid residual only",
     dict(novelty=2, causal_clarity=2, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("neighbor_identity_churn", "neighbor_identity_dynamics",
     "Turnover in an asset's strongest residual neighbors, with positive residual trend, is cluster-membership change rather than static isolation.",
     "rotate neighbor-churn scores across currently eligible identities",
     dict(novelty=2, causal_clarity=2, falsifiability=2, parameter_economy=2, cost_plausibility=2, portfolio_complement=2)),
    ("neighbor_rank_inversion", "neighbor_identity_dynamics",
     "A former top residual neighbor becoming a bottom neighbor is a signed identity reversal.",
     "absolute rank change",
     dict(novelty=2, causal_clarity=2, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("cohort_leader_handoff", "neighbor_identity_dynamics",
     "The residual leader inside a persistent neighbor cohort changing identity is leadership handoff.",
     "shuffle leadership inside the same cohort",
     dict(novelty=2, causal_clarity=1, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("frozen_neighbor_beta", "neighbor_identity_dynamics",
     "Beta to last week's neighbor set, not the current set, measures delayed cluster dependence.",
     "current-neighbor beta",
     dict(novelty=2, causal_clarity=2, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("exclusive_neighbor_gain", "neighbor_identity_dynamics",
     "Gaining residual neighbors that other eligibles do not share is bridge formation.",
     "degree-matched random neighbors",
     dict(novelty=2, causal_clarity=1, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("neighbor_overlap_cash", "neighbor_identity_dynamics",
     "High average neighbor-set overlap across the eligible universe is a cash state.",
     "mean absolute correlation instead of overlap",
     dict(novelty=1, causal_clarity=2, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("rank_stability_breadth", "residual_opportunity_geometry",
     "The fraction of eligible names with stable residual ranks is opportunity density, not residual dispersion.",
     "residual-variance breadth",
     dict(novelty=2, causal_clarity=2, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("failed_recovery_count", "residual_opportunity_geometry",
     "Repeated failed recoveries after a defined residual shock identify exhaustion rather than dip-buying.",
     "shock depth alone",
     dict(novelty=2, causal_clarity=2, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("path_to_range_wedge", "residual_opportunity_geometry",
     "Close-to-close path length rising while high-low range compresses is trapped volatility, not efficiency-ratio trend.",
     "range alone",
     dict(novelty=2, causal_clarity=2, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("signed_gap_persistence", "residual_opportunity_geometry",
     "Persistent overnight gap direction after controlling for residual trend is an opening-state object.",
     "unsigned gap size",
     dict(novelty=1, causal_clarity=1, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
    ("liquidity_age_residual", "residual_opportunity_geometry",
     "Age-since-liquidity-entry only as a conditioner on residual trend, not standalone lifecycle alpha.",
     "current is_liquid only",
     dict(novelty=1, causal_clarity=2, falsifiability=2, parameter_economy=2, cost_plausibility=1, portfolio_complement=1)),
    ("cross_horizon_rank_lock", "residual_opportunity_geometry",
     "Agreement of 7/21/63-day residual ranks with positive slow residual is usable leadership density.",
     "prefer disagreement",
     dict(novelty=1, causal_clarity=2, falsifiability=2, parameter_economy=1, cost_plausibility=1, portfolio_complement=1)),
]

DESIGNS = {
    "clustering_escape": dict(
        incumbent="Frontier-B topology_migration (unsigned degree-centrality change)",
        axes=["information_primitive", "transform"],
        window=63, grid=[42, 63, 84],
        thesis=SLATE[0][2], falsifier=SLATE[0][3],
        transform=(
            "Each Monday t, among assets liquid at t and t-21 with finite residual history, "
            "form residual log returns (own minus equal-liquid market). Compute the W-day residual "
            "correlation matrix on [t-W+1, t] and the matched matrix ending t-21, requiring at least "
            "max(16, W//2) pairwise observations. Local clustering is the Onnela weighted clustering "
            "coefficient of |corr|: elementwise cube-root of clipped |corr|, then diag(W^3) / (k(k-1)) "
            "where k is the number of strictly positive off-diagonal edges. Fragmentation is "
            "max(previous mean |corr| - current mean |corr|, 0). Escape is previous clustering minus "
            "current clustering. Base score = clip(escape, 0, 1) * clip(fragmentation, 0, 1) only if "
            "the 21-day residual sum is positive. Ablation replaces escape with clip(1 - current "
            "clustering, 0, 1) and keeps the fragmentation and residual-trend gates. Falsifier rotates "
            "the escape vector inside the eligible finite cohort before clipping. No extra market-timing gate."
        ),
        ablation="current low clustering level with the same fragmentation and residual-trend gates",
        failure_mode="clustering change restates unsigned centrality migration or residual trend",
    ),
    "factor_loading_escape": dict(
        incumbent="Frontier-B topology_migration / C165 residual-dispersion timing",
        axes=["information_primitive", "transform", "timing_or_state_condition"],
        window=63, grid=[42, 63, 84],
        thesis=SLATE[6][2], falsifier=SLATE[6][3],
        transform=(
            "Same residual and eligibility construction as clustering_escape. On each eligible "
            "finite residual-correlation matrix, compute a symmetric eigendecomposition. Leading "
            "loadings are the absolute values of the eigenvector for the largest eigenvalue. "
            "Spectral gap share is (lambda1-lambda2)/sum(|lambda|). Compression is "
            "max(previous gap share - current gap share, 0). Escape is previous leading loading "
            "minus current leading loading. Base score = clip(escape, 0, 1) * clip(compression, 0, 1) "
            "only if the 21-day residual sum is positive. Ablation uses clip(1 - current loading, 0, 1) "
            "with the same compression and residual-trend gates. Falsifier rotates the loading-change "
            "vector inside the eligible finite cohort. Eigenvector sign is removed by the absolute "
            "value; no extra market-timing gate."
        ),
        ablation="current low leading-factor loading with the same spectral-gap compression gate",
        failure_mode="leading-factor loadings duplicate degree centrality or equal-liquid residual trend",
    ),
    "neighbor_identity_churn": dict(
        incumbent="Frontier-B topology_migration / static low-correlation ranking",
        axes=["information_primitive", "transform", "timing_or_state_condition"],
        window=63, grid=[42, 63, 84],
        thesis=SLATE[12][2], falsifier=SLATE[12][3],
        transform=(
            "Same residual and eligibility construction. For each eligible name, take the three "
            "other names with the largest finite |corr| as the neighbor set (fewer if the cohort "
            "is smaller). Churn is one minus Jaccard overlap of the current and t-21 neighbor "
            "identity sets. Base score = clip(churn, 0, 1) only if the 21-day residual sum is "
            "positive. No global fragmentation gate: neighbor-set turnover is the state. Ablation "
            "scores clip(1 - mean |corr| to other eligibles, 0, 1) with the same residual-trend "
            "gate, i.e. static isolation. Falsifier rotates the churn vector inside the eligible "
            "finite cohort. Neighbor count 3 is a fixed constant."
        ),
        ablation="static isolation (low mean |corr|) with the same residual-trend gate",
        failure_mode="neighbor turnover is a noisy rewrite of low correlation or residual trend",
    ),
    "spectral_gap_cash": dict(
        incumbent="C165 / Frontier-B fragmentation gate",
        axes=["information_primitive", "timing_or_state_condition"],
        window=63, grid=[42, 63, 84],
        thesis=SLATE[7][2], falsifier=SLATE[7][3],
        transform="Deploy residual-trend top-K only when the residual-correlation spectral gap share is falling; cash when it is rising.",
        ablation="always deploy residual trend",
        failure_mode="gap gate restates mean-|corr| fragmentation already used in topology_migration",
        implemented=False,
    ),
    "bridge_betweenness": dict(
        incumbent="Frontier-B topology_migration",
        axes=["information_primitive", "transform"],
        window=63, grid=[42, 63, 84],
        thesis="Rising residual-graph betweenness during fragmentation identifies bridge nodes rather than peripheral nodes.",
        falsifier="rotate betweenness-change",
        transform="Approximate betweenness on a thresholded |corr| graph; score the 21-day increase.",
        ablation="current betweenness level",
        failure_mode="betweenness duplicates degree centrality on a dense crypto graph",
        implemented=False,
    ),
    "failed_recovery_count": dict(
        incumbent="CoCrash126 / unimplemented Frontier-B shock-recovery surface",
        axes=["information_primitive", "transform"],
        window=63, grid=[42, 63, 84],
        thesis=SLATE[19][2], falsifier=SLATE[19][3],
        transform="Count residual shocks that fail to recover half their depth within a fixed horizon; falling failed-count with positive residual is exhaustion relief.",
        ablation="shock depth alone",
        failure_mode="failed-recovery count restates drawdown depth or residual momentum",
        implemented=False,
    ),
}
IMPLEMENTED = ("clustering_escape", "factor_loading_escape", "neighbor_identity_churn")


def base_payload(name, design):
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
            "graph_lag": 21,
            "residual_trend_days": 21,
            "neighbor_count": 3,
            "onnela_clustering": True,
            "leading_factor_absolute_loadings": True,
        },
        folds_allowed_for_selection=["research", "dev"],
        validation="2023-2024 only after freeze; never drives mutation",
        selection_objective="minimum research/dev SR at 4/8/12% ATR costs with existing tie breakers",
        stop_rule="Existing central-parent destructive-control/ablation and 1.0 weak-alpha floor; no parameter expansion after returns; no automatic promotion.",
        ablation=design["ablation"],
        failure_mode=design["failure_mode"],
        cost_hypothesis="Weekly entries, cash, and name caps; exact ATR-linked costs decide viability.",
        portfolio_role="Research satellite on the topology seam that is not unsigned degree-centrality migration",
        source_urls=[],
        source_notes="Original designs from the repository frontier map after A–F. Topology_migration is the nearest successful seam; these objects are local clustering, leading-factor loadings, and neighbor-set identity, not centrality.",
        contamination_notes="A–F research/dev history repeatedly observed. No fresh holdout claim; no live data. Uncommitted G objects are not reused.",
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
        classification_note=(
            "Three discovery hypotheses on the topology seam: Onnela clustering escape, "
            "leading residual-factor loading escape, and residual neighbor-set identity churn."
        ),
    )
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    plan = dict(
        campaign=CAMPAIGN,
        frozen_before_new_returns=True,
        secondary_diagnostics=dict(block_days=21, bootstrap_replicates=2000, seed=20260914),
        progression=(
            "Require all valid cells, central base beating both matched controls, >=2 base robust "
            "Sharpes >=1 and positive central dev residual SR. Only then test one extra execution "
            "day with SAME frozen parameters. Only survivors may receive a separately labeled "
            "contaminated 2023-2024 diagnostic; no 2025+ or live retrieval."
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
