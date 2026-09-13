from __future__ import annotations

import json

from scripts.build_reproducibility_health import DATA_OUT, MARKDOWN_OUT, build_payload, render


def test_reproducibility_artifacts_are_current():
    payload = build_payload()
    assert json.loads(DATA_OUT.read_text()) == payload
    assert MARKDOWN_OUT.read_text() == render(payload)


def test_frontier_k_replay_is_decision_stable_but_not_same_context():
    payload = build_payload()
    assert payload["status"] == "DECISION_STABLE_CONTEXT_DRIFT"
    assert payload["summary"]["decision_stable_count"] == payload["summary"]["families_compared"] == 3
    assert payload["summary"]["identity_stable_count"] == 3
    assert payload["summary"]["max_abs_summary_metric_delta"] < 1e-6
    context = payload["context"]
    assert context["manifest_hash_match"] is True
    assert context["strategy_source_hashes_match"] is True
    assert context["data_hash_match"] is False
    assert context["benchmark_source_hash_match"] is False
    assert context["fold_policy_match"] is True
    assert context["cost_policy_match"] is True
