"""Control-plane tests: triage is deterministic and never cross-ranks hidden evidence."""
import json
from pathlib import Path

from research.lab import compare, pareto_frontier, triage

ROOT = Path(__file__).resolve().parents[1]


def row(cid, score, dd, turn, status="COMPLETE", family="f", mode="base"):
    return {"id": cid, "family": family, "mode": mode, "status": status,
            "selection_score": score, "worst_drawdown_12": dd, "mean_turnover_12": turn}


def test_pareto_has_no_weighted_mega_score():
    rows = [
        row("fast", 1.5, -0.5, .08),
        row("slow", 1.3, -0.3, .03),
        row("dominated", 1.0, -0.6, .10),
    ]
    assert pareto_frontier(rows) == {"fast", "slow"}
    actions = {r["id"]: r["action"] for r in triage({"candidates": rows})}
    assert actions == {"fast": "FORWARD_TEST", "slow": "FORWARD_TEST", "dominated": "HOLD_DOMINATED"}


def test_failed_base_is_repair_and_weak_base_is_killed():
    rows = [
        row("broken", None, None, None, status="FAILED_INTEGRITY"),
        row("weak", .7, -.2, .02),
        row("control", .2, -.1, .01, mode="falsifier"),
    ]
    actions = {r["id"]: r["action"] for r in triage({"candidates": rows})}
    assert actions["broken"] == "REPAIR"
    assert actions["weak"] == "KILL_WEAK_ALPHA"
    assert actions["control"] == "CONTROL"


def test_compare_refuses_false_exactness_when_method_changes():
    base = {"context": {"data_sha256": "d", "manifest_sha256": "m", "folds": [1], "costs": [.04],
                         "source_hashes": {"research/benchmark.py": "a"}},
            "candidates": [row("x", 1.1, -.2, .02)]}
    newer = json.loads(json.dumps(base))
    newer["context"]["source_hashes"]["research/benchmark.py"] = "b"
    newer["candidates"][0]["selection_score"] = 1.2
    result = compare(base, newer)
    assert result["comparability"] == "METHODOLOGY_OR_SOURCE_DELTA"
    assert result["candidate_deltas"][0]["selection_score_delta"] == 0.1


def test_current_canonical_matrix_triages_topology_without_tuning():
    payload = json.loads((ROOT / "docs/data/strategy_matrix.json").read_text())
    actions = {r["id"]: r for r in triage(payload)}
    assert actions["topology_migration_w84"]["action"] == "FORWARD_TEST"
    assert actions["topology_migration_w63"]["action"] == "FORWARD_TEST"
    assert actions["topology_migration_w42"]["action"] == "REPAIR"
    assert actions["liquidity_hysteresis_w42"]["action"] == "KILL_WEAK_ALPHA"
    assert actions["shock_recovery_surface_w42"]["action"] == "REPAIR"
