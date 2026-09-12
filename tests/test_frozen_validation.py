import json
from pathlib import Path

import pytest

from research.frozen_validation import (
    DEFAULT_OBSERVED_STATUS,
    DEFAULT_PLAN,
    load_observed_status,
    load_plan,
    run,
    validation_fold_is_spent,
)


ROOT = Path(__file__).resolve().parents[1]


def test_topology_migration_validation_plan_was_frozen_before_open():
    plan = load_plan(DEFAULT_PLAN)
    # This is historical freeze-time state. Current observation state lives in
    # DEFAULT_OBSERVED_STATUS and must not be inferred from this immutable plan.
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


def test_2023_2024_forward_fold_is_durably_marked_spent():
    observed = load_observed_status(DEFAULT_OBSERVED_STATUS)
    assert validation_fold_is_spent()
    assert observed["evidence_stage"] == "PREREGISTERED_FORWARD_OBSERVED"
    assert observed["fold_status"] == "SPENT_DO_NOT_MUTATE"
    assert observed["decision"] == "FAIL_FORWARD_GATE"
    assert observed["selected_development_candidate"] == "topology_migration_w84"
    assert observed["selected_forward_sharpe_12"] == pytest.approx(0.314)
    assert observed["mutation_policy"] == {
        "use_2023_2024_for_new_strategy_selection": False,
        "retune_topology_migration_from_this_result": False,
        "switch_selected_window_after_observation": False,
        "open_2025_plus_for_repair": False,
    }


def test_normal_validator_refuses_to_reopen_spent_fold(tmp_path):
    with pytest.raises(RuntimeError, match="already observed and permanently spent"):
        run(DEFAULT_PLAN, tmp_path)
    assert list(tmp_path.iterdir()) == []
