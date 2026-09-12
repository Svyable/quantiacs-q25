"""Contract tests for the one-time frozen topology-migration validation gate."""
import json
from pathlib import Path

from research.benchmark import ROOT
from research.preregister import sha256_file

PLAN_PATH = ROOT / "experiments/topology_forward_20260912/validation_plan.json"


def test_validation_plan_is_frozen_and_does_not_open_diagnostic_or_live():
    plan = json.loads(PLAN_PATH.read_text())
    assert plan["created_before_validation_returns"] is True
    assert plan["selected_candidate_before_validation"] == "topology_migration_w84"
    assert plan["validation_fold"] == {"start": "2023-01-01", "end": "2024-12-31"}
    assert plan["cost_ladder"] == [0.0, 0.04, 0.08, 0.12]
    assert plan["forward_gate"]["no_window_switching_after_validation"] is True
    text = PLAN_PATH.read_text().lower()
    assert "2025+" in text
    assert "live" in text


def test_validation_reuses_exact_frontier_b_source_and_preregistration():
    plan = json.loads(PLAN_PATH.read_text())
    prereg = ROOT / plan["source_preregistration"]
    source = ROOT / plan["source_strategy"]
    assert sha256_file(prereg) == plan["source_preregistration_sha256"]
    assert plan["source_preregistration_sha256"] in source.read_text()
    assert "frontier_20260910b_topology_migration" in source.read_text()
    assert not source.name.startswith("topology_forward")


def test_validation_objects_cannot_select_a_new_window():
    plan = json.loads(PLAN_PATH.read_text())
    rows = plan["objects"]
    bases = [row for row in rows if row["mode"] == "base"]
    assert [row["params"]["window"] for row in bases] == [42, 63, 84]
    assert all(row["params"]["top_k"] == 5 for row in rows)
    assert {row["mode"] for row in rows} == {"base", "ablation", "falsifier"}
    assert plan["selected_candidate_before_validation"] == "topology_migration_w84"


def test_runner_is_validation_only_and_reuses_exact_quantiacs_evaluator():
    source = (ROOT / "scripts/validate_topology_forward.py").read_text()
    assert 'max_date=fold["end"]' in source
    assert 'data.sel(time=slice("2015-01-01", fold["end"]))' in source
    assert source.count("cryptodaily_load_data(") == 1
    assert '"2023-01-01"' not in source  # dates live in the frozen plan, not hidden code
    assert "QuantiacsEvaluator" in source
    assert "control_weights" in source
    assert "check_causality" in source
    assert "API_KEY" not in source  # runner delegates public/default access to factory.runner
