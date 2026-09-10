"""Build the public research matrix from canonical repo evidence.

This script never runs a backtest and never invents missing metrics. It only renders
dated evidence that already exists in configs/ and evidence/.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL = ROOT / "configs" / "historical_top10.yaml"
FRONTIER_B = ROOT / "evidence" / "frontier_20260910b" / "observed.json"
DOC = ROOT / "docs" / "RESEARCH_MATRIX.md"
DATA = ROOT / "docs" / "data" / "strategy_matrix.json"


def load():
    return yaml.safe_load(HISTORICAL.read_text()), json.loads(FRONTIER_B.read_text())


def f3(value):
    return "—" if value is None else f"{value:.3f}"


def pct(value):
    return "—" if value is None else f"{100 * value:.1f}%"


def build_payload(historical, frontier):
    legacy = []
    for row in historical["strategies"]:
        legacy.append({
            "lane": "historical_frozen", "rank": row["rank"], "id": row["id"],
            "name": row["name"], "role": row["role"], "full_sharpe": row["full_sharpe"],
            "max_drawdown": row["max_drawdown"], "stress_sharpe": row["stress_sharpe"],
            "stress_atr_fraction": row["stress_atr_fraction"], "status": row["status"],
            "evidence_as_of": historical["as_of"],
        })
    development = []
    for row in frontier["rows"]:
        if row["status"] != "COMPLETE":
            development.append({
                "lane": "development_observed", "rank": None, "id": row["id"],
                "family": row["family"], "mode": row["mode"], "status": row["status"],
                "selection_score": None, "failure_type": row.get("failure_type"),
            })
            continue
        development.append({
            "lane": "development_observed", "rank": None, "id": row["id"],
            "family": row["family"], "mode": row["mode"], "status": row["status"],
            "selection_score": row["selection_score"],
            "research_sharpe_12": row["research"]["sharpe_12"],
            "dev_sharpe_12": row["dev"]["sharpe_12"],
            "research_max_drawdown_12": row["research"]["max_drawdown_12"],
            "dev_max_drawdown_12": row["dev"]["max_drawdown_12"],
            "research_turnover_12": row["research"]["avg_turnover_12"],
            "dev_turnover_12": row["dev"]["avg_turnover_12"],
        })
    rankable = [r for r in development if r["mode"] == "base" and r["selection_score"] is not None]
    rankable.sort(key=lambda r: (-r["selection_score"], r["id"]))
    for i, row in enumerate(rankable, 1):
        row["rank"] = i
    return {
        "schema_version": 1,
        "generated_from": {"historical": str(HISTORICAL.relative_to(ROOT)), "frontier_b": str(FRONTIER_B.relative_to(ROOT))},
        "rules": {
            "do_not_cross_rank_lanes": True,
            "development_selection_score": "minimum Sharpe across research/dev folds at 4%, 8%, and 12% ATR-linked slippage",
            "historical_note": "frozen legacy evidence; not recomputed by current harness",
        },
        "historical_frozen": legacy, "development_observed": development,
        "frontier_source": frontier["source"], "frontier_interpretation": frontier["interpretation"],
    }


def build_markdown(payload):
    base_rows = [r for r in payload["development_observed"] if r["mode"] == "base"]
    base_rows.sort(key=lambda r: (r["rank"] is None, r["rank"] or 999, r["id"]))
    failed = [r for r in payload["development_observed"] if r["status"] != "COMPLETE"]
    controls = [r for r in payload["development_observed"] if r["mode"] in {"control", "ablation", "falsifier"} and r["status"] == "COMPLETE"]
    lines = [
        "---", "title: Research Matrix",
        "description: Evidence-aware ranking of frozen Q25 incumbents and current development candidates.",
        "---", "", "# Q25 research matrix", "",
        "> **Two lanes, never one fake leaderboard.** Frozen historical incumbents and current development candidates use different evidence vintages and harnesses. We rank *within* a comparable lane and show evidence quality beside strategy quality.",
        "", "## Current development candidates", "",
        "The development score is the **worst Sharpe across the 2016–2020 research fold and 2021–2022 dev fold at 4%, 8%, and 12% ATR-linked slippage**. That is deliberately harsher than headline full-period Sharpe.", "",
        "| Dev rank | Candidate | Family | Robust SR | Research SR @12% | Dev SR @12% | Research DD @12% | Dev DD @12% | Status |",
        "|---:|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for r in base_rows:
        lines.append(
            f"| {r['rank'] or '—'} | `{r['id']}` | {r['family']} | {f3(r.get('selection_score'))} | "
            f"{f3(r.get('research_sharpe_12'))} | {f3(r.get('dev_sharpe_12'))} | "
            f"{pct(r.get('research_max_drawdown_12'))} | {pct(r.get('dev_max_drawdown_12'))} | {r['status']} |"
        )
    lines += [
        "", "**Read-through:** topology migration is the only Frontier-B base family with valid cells above the internal 1.0 development floor. `topology_migration_w84` is the strongest observed cell, but it is still development evidence: drawdown is material, one neighboring grid cell failed integrity, and validation / recent diagnostics / current uniqueness are untouched.",
        "", "Liquidity hysteresis is currently a useful state variable, not a standalone alpha candidate: all three valid windows collapse to the same weak robust score. Shock-recovery base cells are not economically adjudicated because their implementation/integrity checks failed in this artifact.",
        "", "## Controls and destructive tests", "",
        "| Object | Type | Robust SR | Research SR @12% | Dev SR @12% | Purpose |",
        "|---|---|---:|---:|---:|---|",
    ]
    purpose = {
        "persistent_low_vol": "low-novelty economic control",
        "topology_migration_ablation": "remove migration component",
        "topology_migration_falsifier": "destroy topology assignment",
        "liquidity_hysteresis_ablation": "remove hysteresis distinction",
        "liquidity_hysteresis_falsifier": "flip lifecycle premise",
        "shock_recovery_surface_falsifier": "destroy recovery premise",
    }
    for r in sorted(controls, key=lambda x: (x["family"], x["id"])):
        lines.append(f"| `{r['id']}` | {r['mode']} | {f3(r.get('selection_score'))} | {f3(r.get('research_sharpe_12'))} | {f3(r.get('dev_sharpe_12'))} | {purpose.get(r['id'], 'control')} |")
    lines += [
        "", "## Frozen historical incumbents", "",
        "These rows are the dated August-2026 research roster. They are not silently recomputed or cross-ranked against Frontier-B development scores.", "",
        "| Frozen rank | Strategy | Role | Full SR | Stress SR | Max DD | Evidence status |",
        "|---:|---|---|---:|---:|---:|---|",
    ]
    for r in payload["historical_frozen"]:
        lines.append(f"| {r['rank']} | **{r['name']}** | {r['role']} | {r['full_sharpe']:.3f} | {r['stress_sharpe']:.3f} @ {100*r['stress_atr_fraction']:.0f}% ATR | {100*r['max_drawdown']:.1f}% | {r['status']} |")
    lines += [
        "", "## Evidence health", "",
        f"Frontier-B observed artifact: workflow run **{payload['frontier_source']['workflow_run_id']}**, artifact **{payload['frontier_source']['artifact_id']}**, Quantiacs access **`{payload['frontier_source']['access_mode']}`**, data hash `{payload['frontier_source']['data_sha256'][:16]}…`.", "",
        f"The artifact contains **{payload['frontier_interpretation']['rankable_complete_cells']} completed cells** and **{payload['frontier_interpretation']['failed_cells']} failed cells**. Failed cells stay visible. A software/integrity failure is not converted into a bad Sharpe, and it does not automatically falsify every other preregistered cell in the mechanism family.", "",
        "The next harness version emits a candidate packet for every attempted cell with strategy quality, evidence completeness, implementation health, cost ladder, drawdown, turnover, causality and provenance. Missing fields remain missing; they are never imputed to make a matrix look complete.", "",
        "[Back to Quant Lab](index.md) · [Evidence model](EVIDENCE_MODEL.md) · [Strategy atlas](STRATEGY_ATLAS.md) · [Testing pyramid](TESTING_PYRAMID.md)",
    ]
    if failed:
        lines += ["", "### Invalid cells retained for repair", "", "| Cell | Family | Failure |", "|---|---|---|"]
        for r in sorted(failed, key=lambda x: x["id"]):
            lines.append(f"| `{r['id']}` | {r['family']} | {r.get('failure_type') or r['status']} |")
    return "\n".join(lines) + "\n"


def render():
    historical, frontier = load()
    payload = build_payload(historical, frontier)
    return payload, build_markdown(payload)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true", help="fail if checked-in generated files are stale")
    args = p.parse_args()
    payload, markdown = render()
    json_text = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.check:
        if not DOC.exists() or DOC.read_text() != markdown:
            raise SystemExit("docs/RESEARCH_MATRIX.md is stale; run scripts/build_research_dashboard.py")
        if not DATA.exists() or DATA.read_text() != json_text:
            raise SystemExit("docs/data/strategy_matrix.json is stale; run scripts/build_research_dashboard.py")
        print("research dashboard is current")
        return
    DOC.parent.mkdir(parents=True, exist_ok=True)
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DOC.write_text(markdown)
    DATA.write_text(json_text)
    print(DOC)
    print(DATA)


if __name__ == "__main__":
    main()
