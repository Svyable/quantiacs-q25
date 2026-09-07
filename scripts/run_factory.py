#!/usr/bin/env python3
"""Run one evolution generation (mutate / grid / render / register).

Does NOT run Quantiacs backtests by default — only creates strategy files
and registry entries with empty metrics placeholders.

Usage:
  python scripts/run_factory.py
  python scripts/run_factory.py --top-n 3 --mutants 2 --seed 42
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from factory.evolve import run_generation
from factory.ideas import SEED_IDEAS, load_ideas
from factory.registry import Registry


def main() -> int:
    parser = argparse.ArgumentParser(description="One Q25 factory evolution generation")
    parser.add_argument("--top-n", type=int, default=3)
    parser.add_argument("--mutants", type=int, default=2, help="Mutants per parent")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--no-grid", action="store_true")
    parser.add_argument("--no-render", action="store_true")
    args = parser.parse_args()

    ideas_path = ROOT / "ideas" / "ideas.jsonl"
    pool = load_ideas(ideas_path) or list(SEED_IDEAS)
    reg = Registry(ROOT / "results" / "registry.jsonl")

    children = run_generation(
        ideas=pool,
        top_n=args.top_n,
        mutants_per_parent=args.mutants,
        use_grid=not args.no_grid,
        seed=args.seed,
        registry=reg,
        ideas_path=ideas_path,
        render=not args.no_render,
    )

    print(f"Generation complete: {len(children)} child ideas")
    for c in children:
        print(f"  - {c.id}  family={c.family}  params={c.params}")
    print(f"Ideas ledger: {ideas_path}")
    print(f"Registry:     {reg.path}")
    print("Metrics are placeholders until a real qnt backtest is run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
