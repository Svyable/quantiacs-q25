"""Research control plane: deterministic triage, Pareto screen, drift compare, failures.

This module never invents alpha scores. It consumes existing evidence artifacts and
turns them into transparent next actions. Development evidence remains development.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

DEVELOPMENT_FLOOR = 1.0


def load_json(path):
    return json.loads(Path(path).read_text())


def candidates(payload):
    if "candidates" in payload:
        return payload["candidates"]
    if "development_observed" in payload:
        return payload["development_observed"]
    if "rows" in payload:
        return payload["rows"]
    raise ValueError("unrecognized evidence payload: no candidate rows")


def _worst_dd(row):
    if row.get("worst_drawdown_12") is not None:
        return row["worst_drawdown_12"]
    vals = [row.get("research_max_drawdown_12"), row.get("dev_max_drawdown_12")]
    vals = [v for v in vals if v is not None]
    return min(vals) if vals else None


def _turnover(row):
    if row.get("mean_turnover_12") is not None:
        return row["mean_turnover_12"]
    vals = [row.get("research_turnover_12"), row.get("dev_turnover_12")]
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals) if vals else None


def _valid_base(row):
    return row.get("mode") == "base" and row.get("status") == "COMPLETE" and row.get("selection_score") is not None


def pareto_frontier(rows):
    """Max robust Sharpe and drawdown quality, min turnover. No weighted mega-score."""
    bases = [r for r in rows if _valid_base(r) and _worst_dd(r) is not None and _turnover(r) is not None]
    ids = set()
    for row in bases:
        dominated = False
        a = (row["selection_score"], _worst_dd(row), _turnover(row))
        for other in bases:
            if other["id"] == row["id"]:
                continue
            b = (other["selection_score"], _worst_dd(other), _turnover(other))
            weak = b[0] >= a[0] and b[1] >= a[1] and b[2] <= a[2]
            strict = b[0] > a[0] or b[1] > a[1] or b[2] < a[2]
            if weak and strict:
                dominated = True
                break
        if not dominated:
            ids.add(row["id"])
    return ids


def triage(payload, development_floor=DEVELOPMENT_FLOOR):
    rows = candidates(payload)
    frontier = pareto_frontier(rows)
    out = []
    for row in rows:
        mode, status, score = row.get("mode"), row.get("status"), row.get("selection_score")
        action, reason = "CONTROL", "destructive/control evidence; do not promote as alpha"
        if mode == "base" and status != "COMPLETE":
            action, reason = "REPAIR", "base economics unknown because implementation/evaluation did not complete"
        elif mode == "base" and score is None:
            action, reason = "HOLD", "base completed without rankable economic packet"
        elif mode == "base" and score < development_floor:
            action, reason = "KILL_WEAK_ALPHA", f"robust development Sharpe below predefined {development_floor:.1f} floor"
        elif mode == "base" and row["id"] in frontier:
            action, reason = "FORWARD_TEST", "valid base sits on transparent development Pareto frontier; use untouched forward evidence, not retuning"
        elif mode == "base":
            action, reason = "HOLD_DOMINATED", "valid base is dominated on robust Sharpe/drawdown/turnover by another current base"
        out.append({
            "id": row.get("id"), "family": row.get("family"), "mode": mode,
            "status": status, "action": action, "reason": reason,
            "selection_score": score, "worst_drawdown_12": _worst_dd(row),
            "mean_turnover_12": _turnover(row), "pareto": row.get("id") in frontier,
            "failure_stage": row.get("failure_stage"), "failure_type": row.get("failure_type"),
        })
    priority = {"REPAIR": 0, "FORWARD_TEST": 1, "KILL_WEAK_ALPHA": 2, "HOLD_DOMINATED": 3, "HOLD": 4, "CONTROL": 5}
    return sorted(out, key=lambda r: (priority[r["action"]], r.get("family") or "", r.get("id") or ""))


def _context(payload):
    return payload.get("context") or payload.get("source") or payload.get("frontier_source") or {}


def compare(old, new):
    """Compare evidence snapshots while making comparability explicit."""
    a, b = _context(old), _context(new)
    structural = ["data_sha256", "manifest_sha256", "folds", "costs"]
    same_structure = all(a.get(k) == b.get(k) for k in structural if k in a or k in b)
    same_sources = a.get("source_hashes") == b.get("source_hashes") if ("source_hashes" in a or "source_hashes" in b) else None
    if same_structure and same_sources is True:
        comparability = "EXACT_REPLAY_CONTEXT"
    elif same_structure:
        comparability = "METHODOLOGY_OR_SOURCE_DELTA"
    else:
        comparability = "NOT_DIRECTLY_COMPARABLE"
    old_rows = {r.get("id"): r for r in candidates(old)}
    new_rows = {r.get("id"): r for r in candidates(new)}
    deltas = []
    for cid in sorted(set(old_rows) | set(new_rows)):
        x, y = old_rows.get(cid), new_rows.get(cid)
        if x is None:
            deltas.append({"id": cid, "change": "ADDED", "old_status": None, "new_status": y.get("status")})
            continue
        if y is None:
            deltas.append({"id": cid, "change": "REMOVED", "old_status": x.get("status"), "new_status": None})
            continue
        oscore, nscore = x.get("selection_score"), y.get("selection_score")
        delta = None if oscore is None or nscore is None else nscore - oscore
        changed = x.get("status") != y.get("status") or delta not in (None, 0)
        if changed:
            deltas.append({
                "id": cid, "change": "CHANGED", "old_status": x.get("status"), "new_status": y.get("status"),
                "old_selection_score": oscore, "new_selection_score": nscore, "selection_score_delta": delta,
            })
    return {"comparability": comparability, "structural_context_equal": same_structure,
            "source_hashes_equal": same_sources, "candidate_deltas": deltas}


def failure_rows(payload):
    return [r for r in candidates(payload) if r.get("status") != "COMPLETE" and r.get("mode") in {"base", "control", "ablation", "falsifier"}]


def markdown_status(payload):
    rows = triage(payload)
    lines = ["# Lab control status", "", "Deterministic next-action queue from recorded evidence; not a promotion decision.", "",
             "| Action | Candidate | Family | Robust SR | Pareto | Reason |",
             "|---|---|---|---:|:---:|---|"]
    for r in rows:
        score = "—" if r["selection_score"] is None else f'{r["selection_score"]:.3f}'
        lines.append(f'| **{r["action"]}** | `{r["id"]}` | {r["family"]} | {score} | {"✓" if r["pareto"] else ""} | {r["reason"]} |')
    return "\n".join(lines) + "\n"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    status = sub.add_parser("status")
    status.add_argument("evidence", type=Path, nargs="?", default=Path("docs/data/strategy_matrix.json"))
    status.add_argument("--json", action="store_true")
    comp = sub.add_parser("compare")
    comp.add_argument("old", type=Path)
    comp.add_argument("new", type=Path)
    failures = sub.add_parser("failures")
    failures.add_argument("evidence", type=Path)
    args = p.parse_args(argv)
    if args.command == "status":
        payload = load_json(args.evidence)
        print(json.dumps(triage(payload), indent=2, sort_keys=True) if args.json else markdown_status(payload), end="")
    elif args.command == "compare":
        print(json.dumps(compare(load_json(args.old), load_json(args.new)), indent=2, sort_keys=True))
    else:
        print(json.dumps(failure_rows(load_json(args.evidence)), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
