import json
from pathlib import Path

from scripts.build_methodology_health import render


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data" / "methodology_health.json"
MARKDOWN = ROOT / "docs" / "METHODOLOGY_HEALTH.md"


def test_methodology_health_artifacts_are_current():
    payload, markdown = render()
    assert json.loads(DATA.read_text()) == payload
    assert MARKDOWN.read_text() == markdown


def test_latest_evidence_and_full_matrix_tier_are_distinct():
    payload, _ = render()
    latest = payload["latest_evidence"]
    health = payload["surface_health"]

    assert latest["campaign"] == "frontier_20260912i"
    assert latest["kind"] == "summary_only"
    assert latest["decision"] == "PROMOTE_ZERO_FREEZE_ALL"
    assert health["latest_full_matrix_campaign"] == "frontier_20260911h"
    assert health["summary_only_latest"] is True
    assert health["research_matrix_mentions_latest"] is False
    assert health["index_mentions_latest"] is True


def test_latest_campaign_rank_is_local_and_guardrail_first():
    payload, _ = render()
    policy = payload["ranking_policy"]
    rows = payload["latest_evidence"]["family_triage"]

    assert policy["cross_campaign_ranking"] == "forbidden"
    assert policy["weighted_megascore"] is False
    assert policy["robust_floor"] == 1.0
    assert [row["family"] for row in rows] == [
        "partial_edge_entropy",
        "conditional_decoupling",
        "trend_dispersion_gate",
    ]
    assert all(row["guardrail_pass"] is False for row in rows)
    assert [row["campaign_rank"] for row in rows] == [1, 2, 3]


def test_latest_packet_preserves_surviving_seam_without_cross_ranking():
    payload, _ = render()
    leader = payload["surviving_development_seam"]

    assert leader["id"] == "topology_migration_w84"
    assert leader["robust_development_sharpe"] == 1.376
    assert max(
        row["best_robust_sharpe"]
        for row in payload["latest_evidence"]["family_triage"]
    ) == 0.304
