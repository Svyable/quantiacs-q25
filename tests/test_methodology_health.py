import json
from pathlib import Path

from scripts.build_methodology_health import render

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data" / "methodology_health.json"
MARKDOWN = ROOT / "docs" / "METHODOLOGY_HEALTH.md"
INDEX = ROOT / "docs" / "index.md"
EVIDENCE = ROOT / "evidence"
EXPERIMENTS = ROOT / "experiments"


def _measured_campaigns():
    out = []
    for directory in EVIDENCE.glob("frontier_*"):
        if any((directory / name).exists() for name in ("matrix.json", "observed_summary.json", "observed.json")):
            out.append(directory.name)
    return sorted(out)


def test_methodology_health_artifacts_are_current():
    payload, markdown = render()
    assert json.loads(DATA.read_text()) == payload
    assert MARKDOWN.read_text() == markdown


def test_latest_evidence_and_full_matrix_tier_are_derived_from_repo_state():
    payload, _ = render()
    latest = payload["latest_evidence"]
    health = payload["surface_health"]
    measured = _measured_campaigns()
    matrices = sorted(
        directory.name for directory in EVIDENCE.glob("frontier_*")
        if (directory / "matrix.json").exists()
    )

    assert measured
    assert latest["campaign"] == measured[-1]
    assert health["latest_full_matrix_campaign"] == (matrices[-1] if matrices else None)
    assert health["summary_only_latest"] is (latest["kind"] == "summary_only")
    assert health["index_uses_generated_health"] is True


def test_latest_campaign_rank_is_local_guardrail_first_and_exposes_controls():
    payload, _ = render()
    policy = payload["ranking_policy"]
    rows = payload["latest_evidence"]["family_triage"]

    assert policy["cross_campaign_ranking"] == "forbidden"
    assert policy["weighted_megascore"] is False
    assert policy["robust_floor"] == 1.0
    assert [row["campaign_rank"] for row in rows] == list(range(1, len(rows) + 1))
    expected = sorted(
        rows,
        key=lambda row: (
            bool(row["guardrail_pass"]),
            float(row["best_robust_sharpe"]),
            str(row["family"]),
        ),
        reverse=True,
    )
    assert rows == expected
    for row in rows:
        assert row["floor_margin"] == row["best_robust_sharpe"] - policy["robust_floor"]
        if row["falsification_complete"]:
            assert row["control_supported"] == (row["central_control_margin"] > 0)


def test_forward_validation_supersedes_stale_development_survivor_claim():
    payload, _ = render()
    leader = payload["development_leader"]
    feedback = payload["learning_loop"]["validation_feedback"]

    assert leader["id"] == "topology_migration_w84"
    assert leader["state"] == "FAILED_FORWARD_GATE"
    assert leader["active_after_validation"] is False
    assert leader["validation"]["decision"] == "FAIL_FORWARD_GATE"
    assert payload["active_new_alpha_seam"] is None
    assert feedback["active_after_validation"] is False


def test_recursive_learning_vector_and_measurement_queue_follow_manifests():
    payload, _ = render()
    loop = payload["learning_loop"]
    latest = loop["latest_campaign"]
    queue = loop["measurement_queue"]
    latest_campaign = payload["latest_evidence"]["campaign"]

    assert loop["policy"]["aggregate_score"] == "forbidden"
    assert loop["policy"]["optimization_target"] is False
    total = latest["families_measured"]
    for key in ("falsification_coverage", "causal_support", "economic_survival", "promotion_ready", "decision_resolution"):
        assert latest[key]["total"] == total

    expected = sorted(
        path.parent.name for path in EXPERIMENTS.glob("frontier_*/manifest.json")
        if path.parent.name > latest_campaign
    )
    assert [row["campaign"] for row in queue["campaigns"]] == expected
    assert queue["count"] == len(expected)
    assert (queue["next_campaign"]["campaign"] if queue["next_campaign"] else None) == (expected[0] if expected else None)
    for row in queue["campaigns"]:
        assert row["automatic_promotion"] is False
        assert row["selection_folds"] == ["research", "dev"]


def test_homepage_is_bound_to_generated_health_packet():
    text = INDEX.read_text()
    assert "data-q25-dashboard" in text
    assert "data/methodology_health.json" in text
    assert "assets/js/dashboard.js" in text
    assert "zero mega-score" in text.lower()
