import json
from pathlib import Path

from scripts.build_methodology_health import render


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data" / "methodology_health.json"
MARKDOWN = ROOT / "docs" / "METHODOLOGY_HEALTH.md"
INDEX = ROOT / "docs" / "index.md"


def test_methodology_health_artifacts_are_current():
    payload, markdown = render()
    assert json.loads(DATA.read_text()) == payload
    assert MARKDOWN.read_text() == markdown


def test_latest_evidence_and_full_matrix_tier_are_distinct():
    payload, _ = render()
    latest = payload["latest_evidence"]
    health = payload["surface_health"]

    assert latest["campaign"] == "frontier_20260912j"
    assert latest["kind"] == "summary_only"
    assert latest["decision"] == "PROMOTE_ZERO"
    assert latest["evidence_stage"] == "DEVELOPMENT_ONLY"
    assert health["latest_full_matrix_campaign"] == "frontier_20260911h"
    assert health["measured_campaigns_since_full_matrix"] == 2
    assert health["summary_only_latest"] is True
    assert health["research_matrix_mentions_latest"] is False
    assert health["index_uses_generated_health"] is True


def test_latest_campaign_rank_is_local_and_exposes_control_margins():
    payload, _ = render()
    policy = payload["ranking_policy"]
    rows = payload["latest_evidence"]["family_triage"]

    assert policy["cross_campaign_ranking"] == "forbidden"
    assert policy["weighted_megascore"] is False
    assert policy["robust_floor"] == 1.0
    assert [row["family"] for row in rows] == [
        "spectral_diversification_gate",
        "positive_edge_shedding",
        "spectral_residual_momentum",
    ]
    assert all(row["guardrail_pass"] is False for row in rows)
    assert all(row["falsification_complete"] is True for row in rows)
    assert [row["control_supported"] for row in rows] == [False, False, True]
    assert rows[0]["central_control_margin"] == 0.498 - 0.665
    assert rows[2]["central_control_margin"] == 0.6670427141125492 - 0.487


def test_forward_validation_supersedes_stale_development_survivor_claim():
    payload, _ = render()
    leader = payload["development_leader"]
    feedback = payload["learning_loop"]["validation_feedback"]

    assert leader["id"] == "topology_migration_w84"
    assert leader["robust_development_sharpe"] == 1.376
    assert leader["state"] == "FAILED_FORWARD_GATE"
    assert leader["active_after_validation"] is False
    assert leader["validation"]["selected_forward_sharpe_12"] == 0.314
    assert leader["validation"]["decision"] == "FAIL_FORWARD_GATE"
    assert payload["active_new_alpha_seam"] is None
    assert feedback["guidance_superseded_by_newer_validation"] is True


def test_recursive_learning_vector_and_measurement_queue_are_explicit():
    payload, _ = render()
    loop = payload["learning_loop"]
    latest = loop["latest_campaign"]
    queue = loop["measurement_queue"]

    assert loop["policy"]["aggregate_score"] == "forbidden"
    assert loop["policy"]["optimization_target"] is False
    assert latest["falsification_coverage"] == {"count": 3, "total": 3, "rate": 1.0}
    assert latest["causal_support"]["count"] == 1
    assert latest["economic_survival"]["count"] == 0
    assert latest["promotion_ready"]["count"] == 0
    assert latest["decision_resolution"]["count"] == 3
    assert queue["count"] == 1
    assert queue["next_campaign"]["campaign"] == "frontier_20260912k"
    assert queue["next_campaign"]["candidate_count"] == 15
    assert queue["next_campaign"]["family_count"] == 3


def test_homepage_is_bound_to_generated_health_packet():
    text = INDEX.read_text()
    assert "data-q25-dashboard" in text
    assert "data/methodology_health.json" in text
    assert "assets/js/dashboard.js" in text
    assert "Five feedback channels, zero mega-score" in text
