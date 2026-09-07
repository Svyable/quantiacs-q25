#!/usr/bin/env python3
"""Write the initial idea ledger from desk seed proposals.

Usage:
  python scripts/bootstrap_ideas.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from factory.desks import list_desks, propose_all
from factory.ideas import SEED_IDEAS, save_ideas
from factory.registry import Registry, RunRecord


def main() -> int:
    ideas_path = ROOT / "ideas" / "ideas.jsonl"
    save_ideas(SEED_IDEAS, ideas_path)

    reg = Registry(ROOT / "results" / "registry.jsonl")
    # Register seed baselines that already exist as hand-written strategies
    seed_paths = {
        "ensemble__sma_rsi_intersection": "strategies/baseline_sma_rsi.py",
        "momentum__donchian_breakout": "strategies/trend_momentum.py",
        "mean_reversion__rsi_oversold_long": "strategies/mean_reversion.py",
        "risk_parity__vol_scaled_sma": "strategies/vol_scaled_trend.py",
    }
    existing_ids = {r.idea_id for r in reg.load()}
    for idea in SEED_IDEAS:
        if idea.id in existing_ids:
            continue
        path = seed_paths.get(idea.id, "")
        reg.append(
            RunRecord(
                run_id=f"seed_{idea.id}",
                idea_id=idea.id,
                strategy_path=path,
                params=dict(idea.params),
                desk_id=idea.desk_id,
                family=idea.family,
                generation=0,
                metrics={},
                status="registered",
                notes="Seed idea from bootstrap_ideas.py; metrics pending real backtest.",
            )
        )

    print(f"Desks: {len(list_desks())}")
    print(f"Seed specs from desks: {len(propose_all())}")
    print(f"Wrote {len(SEED_IDEAS)} ideas -> {ideas_path}")
    for idea in SEED_IDEAS:
        print(f"  - [{idea.desk_id}] {idea.id}: {idea.thesis[:70]}...")
    print("No backtest metrics claimed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
