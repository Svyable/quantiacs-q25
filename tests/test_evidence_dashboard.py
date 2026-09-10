"""Regression tests for evidence-aware ranking and generated research dashboard."""
import json
import numpy as np
import pandas as pd

from research.benchmark import derived_return_metrics
from research.iteration import family_decisions
from scripts.build_research_dashboard import DATA, DOC, render


def metrics(sharpe):
    row = {
        "sharpe_ratio": sharpe, "mean_return": 0.1, "volatility": 0.2,
        "max_drawdown": -0.2, "equity": 1.2, "avg_turnover": 0.02,
        "cagr": 0.1, "sortino_ratio": 1.1, "calmar_ratio": 0.5, "hit_rate": 0.52,
    }
    return {fold: {cost: dict(row) for cost in ["0.00", "0.04", "0.08", "0.12"]} for fold in ["research", "dev"]}


def test_observed_dashboard_is_generated_from_canonical_evidence():
    payload, markdown = render()
    assert DOC.read_text() == markdown
    assert json.loads(DATA.read_text()) == payload
    assert payload["rules"]["do_not_cross_rank_lanes"] is True
    dev = {r["id"]: r for r in payload["development_observed"]}
    assert dev["topology_migration_w84"]["selection_score"] == 1.376132031691156
    assert dev["topology_migration_w84"]["rank"] == 1
    assert dev["topology_migration_w42"]["status"] == "FAILED"
    assert len(payload["historical_frozen"]) == 10


def test_one_invalid_cell_does_not_economically_falsify_family():
    manifest = {"candidates": [
        {"id": "base_good", "family": "f", "mode": "base", "parent_id": None},
        {"id": "base_invalid", "family": "f", "mode": "base", "parent_id": "base_good"},
        {"id": "ablation", "family": "f", "mode": "ablation", "parent_id": "base_good"},
        {"id": "falsifier", "family": "f", "mode": "falsifier", "parent_id": "base_good"},
    ]}
    records = [
        {"id": "base_good", "family": "f", "mode": "base", "status": "COMPLETE", "metrics": metrics(1.3)},
        {"id": "base_invalid", "family": "f", "mode": "base", "status": "FAILED_INTEGRITY", "metrics": {}},
        {"id": "ablation", "family": "f", "mode": "ablation", "status": "COMPLETE", "metrics": metrics(0.8)},
        {"id": "falsifier", "family": "f", "mode": "falsifier", "status": "COMPLETE", "metrics": metrics(0.4)},
    ]
    decision = family_decisions(manifest, records)[0]
    assert decision["decision"] == "CONTINUE"
    assert decision["decision_code"] == "REPAIR_INVALID_CELLS_THEN_FORWARD"
    assert decision["invalid_cells"] == ["base_invalid"]


def test_weak_valid_family_is_killed_without_parameter_rescue():
    manifest = {"candidates": [
        {"id": "base", "family": "f", "mode": "base", "parent_id": None},
        {"id": "falsifier", "family": "f", "mode": "falsifier", "parent_id": "base"},
    ]}
    records = [
        {"id": "base", "family": "f", "mode": "base", "status": "COMPLETE", "metrics": metrics(0.7)},
        {"id": "falsifier", "family": "f", "mode": "falsifier", "status": "COMPLETE", "metrics": metrics(0.2)},
    ]
    decision = family_decisions(manifest, records)[0]
    assert decision["decision"] == "FREEZE"
    assert decision["decision_code"] == "KILL_WEAK_ALPHA"


def test_return_packet_adds_cagr_sortino_and_hit_rate():
    r = pd.Series([0.01, -0.005, 0.003, -0.002] * 100)
    out = derived_return_metrics(r)
    assert out["cagr"] is not None and np.isfinite(out["cagr"])
    assert out["sortino_ratio"] is not None and np.isfinite(out["sortino_ratio"])
    assert out["hit_rate"] == 0.5
