import json
from pathlib import Path

from scripts.build_methodology_health import ROBUST_FLOOR, render


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data" / "methodology_health.json"
MARKDOWN = ROOT / "docs" / "METHODOLOGY_HEALTH.md"


def test_methodology_health_artifacts_are_current():
    payload, markdown = render()
    assert json.loads(DATA.read_text()) == payload
    assert MARKDOWN.read_text() == markdown


def test_latest_evidence_and_full_matrix_tiers_are_explicit():
    payload, _ = render()
    latest = payload["latest_evidence"]
    health = payload["surface_health"]

    assert latest["campaign"].startswith("frontier_")
    assert latest["kind"] in {"summary_only", "matrix", "matrix_and_summary"}
    assert health["latest_full_matrix_campaign"] is None or health["latest_full_matrix_campaign"] <= latest["campaign"]
    assert health["summary_only_latest"] is (latest["kind"] == "summary_only")
    if latest["kind"] == "summary_only":
        assert health["latest_full_matrix_campaign"] != latest["campaign"]


def test_latest_campaign_rank_is_local_guardrail_first_and_dense():
    payload, _ = render()
    policy = payload["ranking_policy"]
    rows = payload["latest_evidence"]["family_triage"]

    assert policy["cross_campaign_ranking"] == "forbidden"
    assert policy["weighted_megascore"] is False
    assert policy["robust_floor"] == ROBUST_FLOOR == 1.0
    assert rows, "latest measured summary should expose at least one family row"
    assert [row["campaign_rank"] for row in rows] == list(range(1, len(rows) + 1))
    assert all(row["guardrail_pass"] is (row["best_robust_sharpe"] >= ROBUST_FLOOR) for row in rows)
    ordering = [
        (row["guardrail_pass"], row["best_robust_sharpe"], row["family"])
        for row in rows
    ]
    assert ordering == sorted(ordering, reverse=True)


def test_missing_control_metrics_remain_missing_instead_of_imputed():
    payload, _ = render()
    rows = payload["latest_evidence"]["family_triage"]
    for row in rows:
        for field in ("ablation_robust_sharpe", "falsifier_robust_sharpe"):
            value = row[field]
            assert value is None or isinstance(value, (int, float))


def test_surviving_seam_is_structured_and_not_cross_ranked():
    payload, _ = render()
    leader = payload["surviving_development_seam"]
    if leader is not None:
        assert leader.get("id")
        assert leader.get("declared_in_campaign", "frontier_").startswith("frontier_")
    assert payload["ranking_policy"]["cross_campaign_ranking"] == "forbidden"
