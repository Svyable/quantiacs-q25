from __future__ import annotations

import json
from pathlib import Path

from scripts.build_reproducibility_health import DATA_OUT, MARKDOWN_OUT, ROOT, build_payload, render
from scripts.check_campaign_replay import compare


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


def _write_ci_replay_matrix(result_dir: Path) -> Path:
    replay = json.loads((ROOT / "evidence/frontier_20260912k/ci_replay/observed_summary.json").read_text())
    context = json.loads((ROOT / "evidence/frontier_20260912k/ci_replay/context.json").read_text())
    manifest = json.loads((ROOT / "experiments/frontier_20260912k/manifest.json").read_text())
    candidates = []
    family_decisions = []
    for family in replay["families"]:
        family_id = family["family"]
        declared = [row for row in manifest["candidates"] if row["family"] == family_id]
        mode_ids = {row["mode"]: row["id"] for row in declared if row["mode"] != "base"}
        scores = {
            family["best_base_id"]: family["best_robust_sharpe"],
            family["central_id"]: family["central_robust_sharpe"],
            mode_ids["ablation"]: family["ablation_robust_sharpe"],
            mode_ids["falsifier"]: family["falsifier_robust_sharpe"],
        }
        declared_by_id = {row["id"]: row for row in declared}
        for candidate_id, score in scores.items():
            row = declared_by_id[candidate_id]
            candidates.append({
                "id": candidate_id,
                "family": family_id,
                "mode": row["mode"],
                "selection_score": score,
                "status": "COMPLETE",
            })
        family_decisions.append({"family": family_id, "decision_code": family["decision_code"]})
    result_dir.mkdir(parents=True, exist_ok=True)
    path = result_dir / "rankings.json"
    path.write_text(json.dumps({"context": context, "candidates": candidates, "families": family_decisions}))
    return path


def test_live_replay_gate_accepts_context_drift_with_stable_decisions(tmp_path):
    _write_ci_replay_matrix(tmp_path)
    payload = compare("frontier_20260912k", tmp_path)
    assert payload["status"] == "DECISION_STABLE_CONTEXT_DRIFT"
    assert payload["hard_failure"] is False
    assert payload["max_abs_summary_metric_delta"] < 1e-6
    assert all(row["decision_match"] and row["best_base_match"] for row in payload["families"])


def test_live_replay_gate_fails_decision_drift(tmp_path):
    path = _write_ci_replay_matrix(tmp_path)
    matrix = json.loads(path.read_text())
    matrix["families"][0]["decision_code"] = "NEEDS_FORWARD_EVIDENCE"
    path.write_text(json.dumps(matrix))
    payload = compare("frontier_20260912k", tmp_path)
    assert payload["status"] == "DECISION_DRIFT"
    assert payload["hard_failure"] is True


def test_live_replay_gate_fails_when_canonical_central_cell_disappears(tmp_path):
    path = _write_ci_replay_matrix(tmp_path)
    matrix = json.loads(path.read_text())
    canonical = json.loads((ROOT / "evidence/frontier_20260912k/observed_summary.json").read_text())
    central_id = canonical["families"][0]["central_id"]
    matrix["candidates"] = [row for row in matrix["candidates"] if row["id"] != central_id]
    path.write_text(json.dumps(matrix))
    payload = compare("frontier_20260912k", tmp_path)
    assert payload["status"] == "DECISION_DRIFT"
    assert payload["hard_failure"] is True
    assert any(row["central_id_match"] is False for row in payload["families"])
