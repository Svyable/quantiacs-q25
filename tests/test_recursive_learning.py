import json
from pathlib import Path

from scripts.build_recursive_learning import render

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data" / "recursive_learning.json"
MARKDOWN = ROOT / "docs" / "RECURSIVE_LEARNING.md"


def test_recursive_learning_artifacts_are_current():
    payload, markdown = render()
    assert json.loads(DATA.read_text()) == payload
    assert MARKDOWN.read_text() == markdown


def test_recursive_learning_policy_is_diagnostic_only():
    payload, _ = render()
    policy = payload["policy"]
    assert policy["aggregate_score"] == "FORBIDDEN"
    assert policy["cross_campaign_scalar_rank"] == "FORBIDDEN"
    assert policy["optimization_target"] is False


def test_recent_window_is_chronological_and_bounded():
    payload, _ = render()
    campaigns = payload["window_campaigns"]
    assert campaigns == sorted(campaigns)
    assert 1 <= len(campaigns) <= 3
    assert [row["campaign"] for row in payload["campaigns"]] == campaigns


def test_campaign_rates_are_bounded():
    payload, _ = render()
    for row in payload["campaigns"]:
        for key in ("falsification_coverage", "control_support", "economic_survival", "promotion_ready", "decision_resolution"):
            metric = row[key]
            assert 0 <= metric["count"] <= metric["total"]
            if metric["rate"] is not None:
                assert 0 <= metric["rate"] <= 1
        assert row["best_floor_margin"] == row["best_robust_sharpe"] - 1.0


def test_trajectory_delta_is_first_to_latest():
    payload, _ = render()
    for metric in payload["trajectories"].values():
        if metric["first"] is None or metric["latest"] is None:
            assert metric["delta_first_to_latest"] is None
        else:
            assert metric["delta_first_to_latest"] == metric["latest"] - metric["first"]
        assert metric["direction"] in {"UP", "DOWN", "FLAT", "MIXED", "INSUFFICIENT_HISTORY"}


def test_family_novelty_is_labeled_as_lexical_only():
    payload, _ = render()
    novelty = payload["recent_window"]["exact_family_name_novelty"]
    assert novelty["family_instances"] >= novelty["distinct_family_names"]
    assert "Lexical" in novelty["interpretation"]
    assert "not semantic originality" in novelty["interpretation"]


def test_validation_calibration_keeps_stages_distinct():
    payload, _ = render()
    calibration = payload["validation_calibration"]
    assert calibration["observed_gate_count"] == len(calibration["events"])
    for event in calibration["events"]:
        dev = event["development_robust_sharpe"]
        forward = event["forward_sharpe_12"]
        if dev not in (None, 0) and forward is not None:
            assert event["retention_ratio"] == forward / dev
        assert event["fold_status"] is not None


def test_next_actions_are_priority_ordered():
    payload, _ = render()
    actions = payload["next_actions"]
    assert [row["priority"] for row in actions] == sorted(row["priority"] for row in actions)
