import json
from pathlib import Path

from scripts.build_learning_router import render

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data" / "learning_router.json"
MARKDOWN = ROOT / "docs" / "LEARNING_ROUTER.md"


def test_learning_router_artifacts_are_current():
    payload, markdown = render()
    assert json.loads(DATA.read_text()) == payload
    assert MARKDOWN.read_text() == markdown


def test_learning_router_never_becomes_a_strategy_score():
    payload, _ = render()
    policy = payload["policy"]
    assert policy["aggregate_score"] == "FORBIDDEN"
    assert policy["strategy_ranking"] == "OUT_OF_SCOPE"
    assert policy["optimization_target"] is False


def test_measured_evidence_is_ingested_before_more_measurement():
    payload, _ = render()
    pipeline = payload["pipeline"]
    pending = pipeline["pending_canonical_ingest"]
    if pending:
        assert pipeline["bottleneck"]["stage"] == "CANONICAL_INGEST"
        assert payload["router"]["next_action"]["action"] == "INGEST_MEASURED_EVIDENCE"
        assert payload["router"]["next_action"]["campaign"] in {
            row["campaign"] for row in pending
        }


def test_frozen_unmeasured_campaigns_are_not_called_evidence():
    payload, _ = render()
    for row in payload["pipeline"]["frozen_unmeasured"]:
        assert row["campaign"]
        assert row["campaign"] not in {
            item["campaign"]
            for item in payload["pipeline"]["pending_canonical_ingest"]
        }


def test_forward_translation_uncertainty_is_explicit():
    payload, _ = render()
    row = next(
        item for item in payload["belief_updates"]
        if item["id"] == "forward_translation"
    )
    if row["state"] == "ONE_OBSERVED_FAILURE":
        assert "single forward event" in row["uncertainty"].lower()
        assert "not a population estimate" in row["uncertainty"].lower()


def test_new_hypothesis_budget_stays_blocked_while_pipeline_work_exists():
    payload, _ = render()
    actions = payload["pipeline"]["operational_actions"]
    budget = payload["router"]["new_hypothesis_budget"]
    if actions:
        assert budget["state"] == "BLOCKED_BY_EXISTING_EVIDENCE_WORK"


def test_router_preserves_mutation_guardrail():
    payload, _ = render()
    text = payload["router"]["mutation_guardrail"].lower()
    assert "never retune" in text
    assert "frozen or measured" in text


def test_router_commits_to_one_next_action_and_marks_backlog_recomputable():
    payload, markdown = render()
    router = payload["router"]
    assert "current_state_backlog" in router
    assert "after_current" not in router
    assert "recompute after the next evidence transition" in markdown.lower()
