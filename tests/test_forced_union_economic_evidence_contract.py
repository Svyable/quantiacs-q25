import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRE = ROOT / "experiments" / "forced_union_20260922" / "preregistration.json"
RESULT = ROOT / "experiments" / "forced_union_20260922" / "economic_result.json"


def _pre():
    return json.loads(PRE.read_text())


def test_frozen_experiment_requires_fresh_economic_evidence_before_promotion():
    p = _pre()
    assert p["status"] == "FROZEN_BEFORE_NEW_ECONOMIC_MEASUREMENT"
    prior = p["prior_observation_disclosure"]
    assert prior["join_only_was_observed_as_control"] is True
    assert "not fresh evidence" in prior["note"].lower()
    assert "no promotion" in prior["note"].lower()


def test_validation_contract_covers_costs_chronology_controls_and_mechanics():
    p = _pre()
    assert p["advancement_gates"]["selection_2016_2022_sharpe_gt_1_costs"] == [0.04, 0.08, 0.12]
    assert p["chronology"]["research"] == "2016-01-01/2020-12-31"
    assert p["chronology"]["development"] == "2021-01-01/2022-12-31"
    assert p["chronology"]["untouched_live"] == "2026-10-01/2027-01-31"
    assert "score_shuffle_with_selection_held_fixed" in p["destructive_controls"]
    required = set(p["required_mechanics"])
    assert {"prefix_causality", "asset_order_invariance", "long_only_liquid_cap_gross", "terminal_365_day_bounded_replay", "determinism"} <= required


def test_any_economic_result_must_be_fresh_complete_and_adjudicated():
    if not RESULT.exists():
        return
    p = _pre()
    r = json.loads(RESULT.read_text())
    assert r["experiment_id"] == p["experiment_id"]
    assert r["preregistration_canonical_sha256"] == p["preregistration_canonical_sha256"]
    assert r["fresh_measurement"] is True
    assert r["uses_prior_observations_for_promotion"] is False
    assert set(r["cost_sensitivity"]) >= {"0.04", "0.08", "0.12"}
    assert set(p["required_metrics"]) <= set(r["metrics_present"])
    assert set(p["required_mechanics"]) <= set(r["mechanics_passed"])
    assert set(p["destructive_controls"]) <= set(r["controls_measured"])
    assert r["adjudication"] in {"ADVANCE", "FALSIFIED", "BLOCKED"}
    if r["adjudication"] == "ADVANCE":
        assert all(r["advancement_gates"].values())
