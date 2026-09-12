import json
from pathlib import Path

from research.frozen_validation import DEFAULT_PLAN, load_plan


ROOT = Path(__file__).resolve().parents[1]


def test_topology_migration_validation_plan_is_frozen_before_open():
    plan = load_plan(DEFAULT_PLAN)
    assert plan["status"] == "FROZEN_PLAN_BEFORE_VALIDATION_OPEN"
    assert plan["candidate"] == {
        "id": "topology_migration_w84",
        "family": "topology_migration",
        "mode": "base",
        "params": {"top_k": 5, "window": 84},
    }
    assert plan["validation_fold"]["start"] == "2023-01-01"
    assert plan["validation_fold"]["end"] == "2024-12-31"
    assert plan["decision_policy"]["automatic_promotion"] is False
    assert plan["decision_policy"]["soft_validation_threshold"] is None
    assert plan["decision_policy"]["diagnostic_2025_plus"] == "excluded"
    assert plan["decision_policy"]["live_2026_10_01_plus"] == "excluded"


def test_validation_selection_matches_committed_development_evidence():
    plan = load_plan(DEFAULT_PLAN)
    observed = json.loads((ROOT / plan["created_from"]["development_evidence"]).read_text())
    row = next(r for r in observed["rows"] if r["id"] == "topology_migration_w84")
    assert row["status"] == "COMPLETE"
    assert row["selection_score"] == plan["created_from"]["development_selection_score"]
    assert plan["candidate"]["id"] == plan["created_from"]["development_selected_id"]


def test_validation_has_no_search_grid_or_mutation_lane():
    plan = load_plan(DEFAULT_PLAN)
    assert "grid" not in plan
    assert plan["candidate"]["params"] == {"top_k": 5, "window": 84}
    assert plan["decision_policy"]["mutation_after_observation"] == "forbidden"
    assert plan["reporting"]["cross_campaign_megascore"] is False
