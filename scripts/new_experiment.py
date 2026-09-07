#!/usr/bin/env python3
"""CLI: create experiments/<id>/ with preregistration template + formula ledger copy.

Usage:
  python scripts/new_experiment.py --track robustness --mechanism momentum \\
      --thesis "..." --falsifier "..."
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.preregister import load_template, write_preregistration  # noqa: E402


def _slug(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")[:48] or "exp"


def main() -> int:
    p = argparse.ArgumentParser(description="Create a preregistered experiment directory")
    p.add_argument("--track", required=True, choices=["discovery", "robustness"])
    p.add_argument("--mechanism", required=True, help="mechanism family id")
    p.add_argument("--thesis", default="", help="one-line thesis")
    p.add_argument("--falsifier", default="", help="what would kill the thesis")
    p.add_argument("--id", default="", help="optional experiment id (else auto)")
    p.add_argument(
        "--rebalance",
        default="",
        help="rebalance rule (default by track: weekly for robustness, daily for discovery)",
    )
    args = p.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    exp_id = args.id or f"{ts}_{args.track}_{_slug(args.mechanism)}"
    dest = ROOT / "experiments" / exp_id
    if dest.exists():
        print(f"Refusing to overwrite existing {dest}", file=sys.stderr)
        return 1

    dest.mkdir(parents=True)
    tpl = load_template(ROOT)
    tpl["experiment_id"] = exp_id
    tpl["track"] = args.track
    tpl["mechanism"] = args.mechanism
    tpl["thesis"] = args.thesis or tpl.get("thesis") or ""
    tpl["falsifier"] = args.falsifier or tpl.get("falsifier") or ""
    if args.rebalance:
        tpl["rebalance"] = args.rebalance
    else:
        tpl["rebalance"] = "weekly" if args.track == "robustness" else "daily"
    if args.track == "robustness":
        tpl["allocation_rule"] = (
            "capped water-fill; gross<=1; unused=cash; long-only * is_liquid"
        )

    path, digest = write_preregistration(dest, tpl)

    # Copy ledger header for this experiment
    ledger_src = ROOT / "templates" / "formula_ledger.csv"
    ledger_dst = dest / "formula_ledger.csv"
    shutil.copyfile(ledger_src, ledger_dst)

    # PM report stub
    pm_src = ROOT / "templates" / "pm_report.md"
    pm_text = pm_src.read_text(encoding="utf-8").replace("{{experiment_id}}", exp_id)
    (dest / "pm_report.md").write_text(pm_text, encoding="utf-8")

    print(f"Created {dest}")
    print(f"preregistration: {path}")
    print(f"sha256: {digest}")
    print("Fill thesis/falsifier if empty, then run testing pyramid. Do not invent metrics.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
