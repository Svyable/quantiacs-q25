#!/usr/bin/env python3
"""Compare a fresh development run with committed canonical campaign evidence.

Decision/selected-identity drift is a hard failure. Numeric or provenance drift is
reported but kept as a separate evidence-quality context.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
METRIC_FIELDS = (
    "best_robust_sharpe",
    "central_robust_sharpe",
    "ablation_robust_sharpe",
    "falsifier_robust_sharpe",
)


def _load(path: Path) -> Any:
    return json.loads(path.read_text())


def _family_map(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row["family"]): row for row in summary.get("families", [])}


def _summary_from_matrix(matrix: dict[str, Any], canonical: dict[str, Any]) -> dict[str, Any]:
    candidates = matrix.get("candidates", [])
    by_id = {str(row.get("id")): row for row in candidates if row.get("id")}
    by_family: dict[str, list[dict[str, Any]]] = {}
    for row in candidates:
        family = str(row.get("family") or "")
        if family and family != "control":
            by_family.setdefault(family, []).append(row)
    decisions = {str(row["family"]): row for row in matrix.get("families", [])}

    families: list[dict[str, Any]] = []
    for family, expected in _family_map(canonical).items():
        rows = by_family.get(family, [])
        bases = [row for row in rows if row.get("mode") == "base" and row.get("selection_score") is not None]
        best = max(bases, key=lambda row: float(row["selection_score"])) if bases else None
        central = by_id.get(str(expected.get("central_id")))
        ablations = [row for row in rows if row.get("mode") == "ablation"]
        falsifiers = [row for row in rows if row.get("mode") == "falsifier"]
        decision = decisions.get(family, {})
        families.append({
            "family": family,
            "best_base_id": best.get("id") if best else None,
            "best_robust_sharpe": best.get("selection_score") if best else None,
            "central_id": central.get("id") if central else None,
            "central_robust_sharpe": central.get("selection_score") if central else None,
            "ablation_robust_sharpe": ablations[0].get("selection_score") if len(ablations) == 1 else None,
            "falsifier_robust_sharpe": falsifiers[0].get("selection_score") if len(falsifiers) == 1 else None,
            "decision_code": decision.get("decision_code"),
        })
    return {"families": families}


def compare(campaign: str, result_dir: Path) -> dict[str, Any]:
    canonical_dir = ROOT / "evidence" / campaign
    canonical_summary_path = canonical_dir / "observed_summary.json"
    canonical_context_path = canonical_dir / "context.json"
    if not canonical_summary_path.exists() or not canonical_context_path.exists():
        return {
            "schema_version": 1,
            "campaign": campaign,
            "status": "NO_CANONICAL_EVIDENCE",
            "hard_failure": False,
            "reason": "fresh run preserved; no committed canonical summary/context to compare",
        }

    canonical = _load(canonical_summary_path)
    canonical_context = _load(canonical_context_path)
    matrix = _load(result_dir / "rankings.json")
    replay = _summary_from_matrix(matrix, canonical)
    replay_context = matrix.get("context", {})

    expected = _family_map(canonical)
    observed = _family_map(replay)
    rows: list[dict[str, Any]] = []
    deltas: list[float] = []
    hard_failure = False
    for family in sorted(expected):
        left = expected[family]
        right = observed.get(family, {})
        decision_match = left.get("decision_code") == right.get("decision_code")
        best_base_match = left.get("best_base_id") == right.get("best_base_id")
        central_id_match = left.get("central_id") == right.get("central_id")
        metric_deltas = {}
        for field in METRIC_FIELDS:
            a, b = left.get(field), right.get(field)
            if a is None or b is None:
                metric_deltas[field] = None
            else:
                delta = abs(float(a) - float(b))
                metric_deltas[field] = delta
                deltas.append(delta)
        family_hard_failure = not (decision_match and best_base_match and central_id_match)
        hard_failure = hard_failure or family_hard_failure
        rows.append({
            "family": family,
            "decision_match": decision_match,
            "best_base_match": best_base_match,
            "central_id_match": central_id_match,
            "hard_failure": family_hard_failure,
            "metric_deltas": metric_deltas,
            "max_abs_metric_delta": max((v for v in metric_deltas.values() if v is not None), default=None),
        })

    canonical_sources = canonical_context.get("source_hashes", {})
    replay_sources = replay_context.get("source_hashes", {})
    strategy_keys = sorted(key for key in canonical_sources if key.startswith("strategies/generated/"))
    context = {
        "manifest_hash_match": canonical_context.get("manifest_sha256") == replay_context.get("manifest_sha256"),
        "strategy_source_hashes_match": all(canonical_sources.get(key) == replay_sources.get(key) for key in strategy_keys),
        "data_hash_match": canonical_context.get("data_sha256") == replay_context.get("data_sha256"),
        "benchmark_source_hash_match": canonical_sources.get("research/benchmark.py") == replay_sources.get("research/benchmark.py"),
        "iteration_source_hash_match": canonical_sources.get("research/iteration.py") == replay_sources.get("research/iteration.py"),
        "toolbox_stats_hash_match": canonical_context.get("toolbox_stats_sha256") == replay_context.get("toolbox_stats_sha256"),
        "access_mode_match": canonical_context.get("quantiacs_access_mode") == replay_context.get("quantiacs_access_mode"),
        "fold_policy_match": canonical_context.get("folds") == replay_context.get("folds"),
        "cost_policy_match": canonical_context.get("costs") == replay_context.get("costs"),
        "canonical_data_sha256": canonical_context.get("data_sha256"),
        "replay_data_sha256": replay_context.get("data_sha256"),
        "canonical_python": canonical_context.get("python"),
        "replay_python": replay_context.get("python"),
    }
    exact_context = all(context[key] for key in (
        "manifest_hash_match", "strategy_source_hashes_match", "data_hash_match",
        "benchmark_source_hash_match", "iteration_source_hash_match",
        "toolbox_stats_hash_match", "access_mode_match", "fold_policy_match", "cost_policy_match",
    ))
    max_delta = max(deltas) if deltas else None
    if hard_failure:
        status = "DECISION_DRIFT"
    elif exact_context and max_delta == 0:
        status = "IDENTICAL_REPLAY"
    else:
        status = "DECISION_STABLE_CONTEXT_DRIFT"
    return {
        "schema_version": 1,
        "campaign": campaign,
        "status": status,
        "hard_failure": hard_failure,
        "max_abs_summary_metric_delta": max_delta,
        "context": context,
        "families": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", required=True)
    parser.add_argument("--result-dir", required=True, type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    payload = compare(args.campaign, args.result_dir)
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.json_out:
        args.json_out.write_text(text)
    return 2 if payload.get("hard_failure") else 0


if __name__ == "__main__":
    raise SystemExit(main())
