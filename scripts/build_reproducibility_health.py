#!/usr/bin/env python3
"""Build evidence-replay reproducibility telemetry for Frontier-K."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = "frontier_20260912k"
LOCAL_DIR = ROOT / "evidence" / CAMPAIGN
REPLAY_DIR = LOCAL_DIR / "ci_replay"
DATA_OUT = ROOT / "docs" / "data" / "reproducibility_health.json"
MARKDOWN_OUT = ROOT / "docs" / "REPRODUCIBILITY_HEALTH.md"
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


def _strategy_hashes(context: dict[str, Any]) -> dict[str, str]:
    return {
        key: value
        for key, value in context.get("source_hashes", {}).items()
        if key.startswith("strategies/generated/")
    }


def build_payload() -> dict[str, Any]:
    local_summary = _load(LOCAL_DIR / "observed_summary.json")
    replay_summary = _load(REPLAY_DIR / "observed_summary.json")
    local_context = _load(LOCAL_DIR / "context.json")
    replay_context = _load(REPLAY_DIR / "context.json")

    local_families = _family_map(local_summary)
    replay_families = _family_map(replay_summary)
    families = sorted(set(local_families) | set(replay_families))
    rows: list[dict[str, Any]] = []
    all_deltas: list[float] = []

    for family in families:
        left = local_families.get(family)
        right = replay_families.get(family)
        if left is None or right is None:
            rows.append({
                "family": family,
                "present_in_both": False,
                "decision_match": False,
                "best_base_match": False,
                "central_id_match": False,
                "max_abs_metric_delta": None,
            })
            continue
        deltas = [
            abs(float(left[field]) - float(right[field]))
            for field in METRIC_FIELDS
            if left.get(field) is not None and right.get(field) is not None
        ]
        all_deltas.extend(deltas)
        rows.append({
            "family": family,
            "present_in_both": True,
            "decision_local": left.get("decision_code"),
            "decision_replay": right.get("decision_code"),
            "decision_match": left.get("decision_code") == right.get("decision_code"),
            "best_base_local": left.get("best_base_id"),
            "best_base_replay": right.get("best_base_id"),
            "best_base_match": left.get("best_base_id") == right.get("best_base_id"),
            "central_id_match": left.get("central_id") == right.get("central_id"),
            "max_abs_metric_delta": max(deltas) if deltas else None,
        })

    matched = [row for row in rows if row["present_in_both"]]
    decision_stable = bool(rows) and all(row["decision_match"] for row in rows)
    identity_stable = bool(rows) and all(
        row["best_base_match"] and row["central_id_match"] for row in rows
    )
    manifest_match = local_context.get("manifest_sha256") == replay_context.get("manifest_sha256")
    data_hash_match = local_context.get("data_sha256") == replay_context.get("data_sha256")
    access_mode_match = local_context.get("quantiacs_access_mode") == replay_context.get("quantiacs_access_mode")
    fold_policy_match = local_context.get("folds") == replay_context.get("folds")
    cost_policy_match = local_context.get("costs") == replay_context.get("costs")
    strategy_hash_match = _strategy_hashes(local_context) == _strategy_hashes(replay_context)
    benchmark_hash_match = (
        local_context.get("source_hashes", {}).get("research/benchmark.py")
        == replay_context.get("source_hashes", {}).get("research/benchmark.py")
    )
    iteration_hash_match = (
        local_context.get("source_hashes", {}).get("research/iteration.py")
        == replay_context.get("source_hashes", {}).get("research/iteration.py")
    )
    toolbox_hash_match = local_context.get("toolbox_stats_sha256") == replay_context.get("toolbox_stats_sha256")
    max_delta = max(all_deltas) if all_deltas else None

    if not decision_stable or not identity_stable:
        status = "DECISION_DRIFT"
    elif data_hash_match and benchmark_hash_match and max_delta == 0:
        status = "IDENTICAL_REPLAY"
    else:
        status = "DECISION_STABLE_CONTEXT_DRIFT"

    return {
        "schema_version": 1,
        "campaign": CAMPAIGN,
        "status": status,
        "policy": {
            "mix_metrics_across_contexts": False,
            "decision_drift_is_ci_failure": True,
            "context_drift_is_visible": True,
        },
        "summary": {
            "families_compared": len(rows),
            "families_present_in_both": len(matched),
            "decision_stable_count": sum(1 for row in rows if row["decision_match"]),
            "identity_stable_count": sum(
                1 for row in rows if row["best_base_match"] and row["central_id_match"]
            ),
            "max_abs_summary_metric_delta": max_delta,
        },
        "context": {
            "manifest_hash_match": manifest_match,
            "strategy_source_hashes_match": strategy_hash_match,
            "data_hash_match": data_hash_match,
            "benchmark_source_hash_match": benchmark_hash_match,
            "iteration_source_hash_match": iteration_hash_match,
            "toolbox_stats_hash_match": toolbox_hash_match,
            "access_mode_match": access_mode_match,
            "fold_policy_match": fold_policy_match,
            "cost_policy_match": cost_policy_match,
            "local": {
                "data_sha256": local_context.get("data_sha256"),
                "python": local_context.get("python"),
                "benchmark_sha256": local_context.get("source_hashes", {}).get("research/benchmark.py"),
            },
            "ci_replay": {
                "data_sha256": replay_context.get("data_sha256"),
                "python": replay_context.get("python"),
                "benchmark_sha256": replay_context.get("source_hashes", {}).get("research/benchmark.py"),
                "workflow_run": replay_summary.get("workflow_run"),
                "artifact_id": replay_summary.get("artifact_id"),
                "artifact_digest": replay_summary.get("artifact_digest"),
            },
        },
        "families": rows,
    }


def render(payload: dict[str, Any] | None = None) -> str:
    payload = build_payload() if payload is None else payload
    summary = payload["summary"]
    context = payload["context"]
    lines = [
        "# Reproducibility Health",
        "",
        "> Replay consistency is an evidence-quality channel. It is not a strategy-performance score.",
        "",
        f"Campaign: **`{payload['campaign']}`**  ",
        f"Status: **`{payload['status']}`**",
        "",
        "## Replay pulse",
        "",
        "| Check | State |",
        "|---|---|",
        f"| Family decisions stable | **{summary['decision_stable_count']}/{summary['families_compared']}** |",
        f"| Best-base + central identity stable | **{summary['identity_stable_count']}/{summary['families_compared']}** |",
        f"| Max absolute summary-metric delta | **{summary['max_abs_summary_metric_delta']:.3e}** |",
        f"| Manifest hash match | **{'yes' if context['manifest_hash_match'] else 'no'}** |",
        f"| Strategy source hashes match | **{'yes' if context['strategy_source_hashes_match'] else 'no'}** |",
        f"| Data hash match | **{'yes' if context['data_hash_match'] else 'no'}** |",
        f"| Benchmark source hash match | **{'yes' if context['benchmark_source_hash_match'] else 'no'}** |",
        f"| Fold / cost policy match | **{'yes' if context['fold_policy_match'] and context['cost_policy_match'] else 'no'}** |",
        "",
        "## Contexts",
        "",
        f"- Local canonical packet: Python `{context['local']['python']}`, data `{context['local']['data_sha256']}`, benchmark `{context['local']['benchmark_sha256']}`.",
        f"- CI replay: Python `{context['ci_replay']['python']}`, data `{context['ci_replay']['data_sha256']}`, benchmark `{context['ci_replay']['benchmark_sha256']}`; workflow `{context['ci_replay']['workflow_run']}`, artifact `{context['ci_replay']['artifact_id']}`.",
        "",
        "The strategy files and frozen manifest are the same, while the data snapshot and benchmark source context differ. The family decisions remain stable and the observed summary-metric drift is tiny, but the two packets are **not byte-identical reproductions**. Their metrics must remain in separate provenance contexts.",
        "",
        "## Family replay comparison",
        "",
        "| Family | Decision | Best base | Central | Max metric Δ |",
        "|---|---|---|---|---:|",
    ]
    for row in payload["families"]:
        decision = "MATCH" if row["decision_match"] else "DRIFT"
        best = "MATCH" if row["best_base_match"] else "DRIFT"
        central = "MATCH" if row["central_id_match"] else "DRIFT"
        delta = "—" if row["max_abs_metric_delta"] is None else f"{row['max_abs_metric_delta']:.3e}"
        lines.append(f"| `{row['family']}` | {decision} | {best} | {central} | {delta} |")
    lines += [
        "",
        "## Recursive rule",
        "",
        "A replay may confirm a decision without becoming the same evidence packet. Data hash, evaluator hash, source hashes, fold policy, and access mode are evidence-quality dimensions. **Never average, splice, or silently replace metrics across non-identical contexts.** If a replay changes a family decision or selected identity, treat that as decision drift and fail CI until reconciled.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload = build_payload()
    markdown = render(payload)
    json_text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.check:
        stale = []
        if not DATA_OUT.exists() or DATA_OUT.read_text() != json_text:
            stale.append(str(DATA_OUT.relative_to(ROOT)))
        if not MARKDOWN_OUT.exists() or MARKDOWN_OUT.read_text() != markdown:
            stale.append(str(MARKDOWN_OUT.relative_to(ROOT)))
        if stale:
            raise SystemExit("stale reproducibility artifacts: " + ", ".join(stale))
        if payload["status"] == "DECISION_DRIFT":
            raise SystemExit("replay changed family decision or selected identity")
        return 0
    DATA_OUT.parent.mkdir(parents=True, exist_ok=True)
    DATA_OUT.write_text(json_text)
    MARKDOWN_OUT.write_text(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
