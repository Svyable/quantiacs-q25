import json
from pathlib import Path

import yaml

from scripts.build_research_control_plane import render

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data" / "research_control_plane.json"
MARKDOWN = ROOT / "docs" / "RESEARCH_CONTROL_PLANE.md"
HISTORICAL = ROOT / "configs" / "historical_top10.yaml"


def test_research_control_plane_artifacts_are_current():
    payload, markdown = render()
    assert json.loads(DATA.read_text()) == payload
    assert MARKDOWN.read_text() == markdown


def test_control_plane_never_cross_ranks_evidence_lanes():
    payload, _ = render()
    policy = payload["policy"]
    assert policy["cross_campaign_scalar_rank"] == "FORBIDDEN"
    assert policy["weighted_mega_score"] is False
    assert policy["lane_order_is_not_quality_order"] is True
    assert all(row["lane"] == "LATEST_CANONICAL_DEVELOPMENT_CAMPAIGN" for row in payload["canonical_latest"]["family_stack"])
    assert all(row["lane"] == "FROZEN_HISTORICAL_ROSTER" for row in payload["frozen_historical_stack"])


def test_frozen_historical_rank_is_preserved_not_reoptimized():
    payload, _ = render()
    source = yaml.safe_load(HISTORICAL.read_text())["strategies"]
    assert [(row["rank"], row["id"]) for row in payload["frozen_historical_stack"]] == [
        (row["rank"], row["id"]) for row in source
    ]


def test_latest_development_rank_is_campaign_local_and_contiguous():
    payload, _ = render()
    rows = payload["canonical_latest"]["family_stack"]
    assert [row["campaign_rank"] for row in rows] == list(range(1, len(rows) + 1))
    assert all("best_robust_sharpe" in row for row in rows)
    assert all("decision_code" in row for row in rows)


def test_measurement_receipts_change_queue_semantics_without_becoming_canonical():
    payload, _ = render()
    receipts = {row["campaign"]: row for row in payload["measurement_receipts"]}
    queue = {row["campaign"]: row for row in payload["measurement_queue"]}
    for campaign, receipt in receipts.items():
        if campaign not in queue:
            continue
        assert queue[campaign]["measurement_state"] == receipt["status"]
        if receipt["status"] == "MEASURED_AWAITING_CANONICAL_INGEST":
            assert any(
                action["action"] == "INGEST_MEASURED_EVIDENCE" and action["campaign"] == campaign
                for action in payload["dogfood"]["next_actions"]
            )


def test_frontier_label_collisions_are_visible_and_use_full_campaign_uids():
    payload, _ = render()
    for collision in payload["dogfood"]["frontier_label_collisions"]:
        assert len(collision["campaigns"]) > 1
        assert len(set(collision["campaigns"])) == len(collision["campaigns"])
        assert all(campaign.startswith("frontier_") for campaign in collision["campaigns"])
    if payload["dogfood"]["frontier_label_collisions"]:
        assert payload["policy"]["display_rule"].startswith("show campaign UID")


def test_dogfood_actions_are_priority_ordered_and_state_derived():
    payload, _ = render()
    actions = payload["dogfood"]["next_actions"]
    assert [row["priority"] for row in actions] == sorted(row["priority"] for row in actions)
    assert payload["dogfood"]["pending_canonical_ingest_count"] == sum(
        row["status"] == "MEASURED_AWAITING_CANONICAL_INGEST"
        for row in payload["measurement_receipts"]
    )
    assert payload["dogfood"]["unmeasured_queue_count"] == sum(
        row["measurement_state"] == "FROZEN_UNMEASURED_OR_UNRECEIPTED"
        for row in payload["measurement_queue"]
    )
