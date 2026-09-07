"""Evolution: mutate params, spawn variants, rank by gates.

v1 is deterministic mutation + ranked parameter search (no LLM required).
Hooks left for future LLM idea expansion.
"""

from __future__ import annotations

import hashlib
import itertools
import random
from pathlib import Path
from typing import Any, Callable

from .gates import GateResult, evaluate_all, rank_key
from .ideas import Idea, SEED_IDEAS, load_ideas, save_ideas
from .registry import Registry, RunRecord
from .render import render_to_file

ROOT = Path(__file__).resolve().parents[1]
IDEAS_LEDGER = ROOT / "ideas" / "ideas.jsonl"


def _mutate_value(value: float, lo: float, hi: float, rng: random.Random, scale: float = 0.2) -> float:
    """Perturb a numeric param within [lo, hi]."""
    span = hi - lo
    delta = rng.uniform(-scale, scale) * span
    new = value + delta
    return max(lo, min(hi, new))


def mutate_idea(idea: Idea, rng: random.Random | None = None, generation: int | None = None) -> Idea:
    """Create a child Idea with mutated numeric params within declared ranges."""
    rng = rng or random.Random()
    new_params: dict[str, Any] = {}
    for k, v in idea.params.items():
        if k in idea.param_ranges:
            lo, hi = idea.param_ranges[k]
            try:
                fv = float(v)
                mv = _mutate_value(fv, float(lo), float(hi), rng)
                # Keep ints as ints when original looked integral
                if isinstance(v, int) or (isinstance(v, float) and float(v).is_integer() and k != "bb_std"):
                    new_params[k] = int(round(mv))
                else:
                    new_params[k] = round(mv, 4)
            except (TypeError, ValueError):
                new_params[k] = v
        else:
            new_params[k] = v

    gen = generation if generation is not None else idea.generation + 1
    digest = hashlib.sha1(
        f"{idea.id}:{sorted(new_params.items())}:{gen}".encode()
    ).hexdigest()[:8]
    child_id = f"{idea.id}__m{digest}"
    return Idea(
        id=child_id,
        name=f"{idea.name}_m{digest}",
        desk_id=idea.desk_id,
        family=idea.family,
        thesis=idea.thesis + f" [mutated gen={gen}]",
        params=new_params,
        param_ranges=dict(idea.param_ranges),
        template_id=idea.template_id,
        tags=list(idea.tags) + ["mutated"],
        parent_id=idea.id,
        generation=gen,
    )


def grid_variants(idea: Idea, max_variants: int = 8) -> list[Idea]:
    """Small discrete grid over param_ranges (endpoints + mid) for ranked search."""
    axes: dict[str, list[Any]] = {}
    for k, (lo, hi) in idea.param_ranges.items():
        lo_f, hi_f = float(lo), float(hi)
        mid = (lo_f + hi_f) / 2.0
        vals = [lo_f, mid, hi_f]
        if k != "bb_std":
            vals = [int(round(v)) for v in vals]
        else:
            vals = [round(v, 2) for v in vals]
        # Dedup preserving order
        seen: set[Any] = set()
        uniq: list[Any] = []
        for v in vals:
            if v not in seen:
                seen.add(v)
                uniq.append(v)
        axes[k] = uniq

    keys = sorted(axes.keys())
    if not keys:
        return []

    combos = list(itertools.product(*(axes[k] for k in keys)))
    # Cap
    if len(combos) > max_variants:
        # Evenly sample
        step = len(combos) / max_variants
        combos = [combos[int(i * step)] for i in range(max_variants)]

    variants: list[Idea] = []
    for i, combo in enumerate(combos):
        params = dict(idea.params)
        for k, v in zip(keys, combo):
            params[k] = v
        # Skip identical to parent
        if params == idea.params:
            continue
        digest = hashlib.sha1(f"{idea.id}:grid:{i}:{params}".encode()).hexdigest()[:8]
        variants.append(
            Idea(
                id=f"{idea.id}__g{digest}",
                name=f"{idea.name}_g{digest}",
                desk_id=idea.desk_id,
                family=idea.family,
                thesis=idea.thesis + f" [grid variant {i}]",
                params=params,
                param_ranges=dict(idea.param_ranges),
                template_id=idea.template_id,
                tags=list(idea.tags) + ["grid"],
                parent_id=idea.id,
                generation=idea.generation + 1,
            )
        )
    return variants


# Hook for future LLM idea expansion (unused in v1)
LLMIdeaExpander = Callable[[Idea], list[Idea]]


def expand_with_llm(idea: Idea, expander: LLMIdeaExpander | None = None) -> list[Idea]:
    """Optional LLM expansion hook. Returns [] if no expander provided."""
    if expander is None:
        return []
    return expander(idea)


def select_parents(
    ideas: list[Idea],
    registry: Registry,
    top_n: int = 3,
) -> list[Idea]:
    """Rank ideas by latest gate results; fall back to seed order if no metrics."""
    latest = registry.latest_by_idea()
    scored: list[tuple[tuple, Idea]] = []
    for idea in ideas:
        rec = latest.get(idea.id)
        if rec and rec.metrics:
            gr = GateResult(
                hard_pass=bool(rec.hard_pass),
                soft_pass=bool(rec.soft_pass),
                hard_failures=list(rec.hard_failures),
                soft_failures=list(rec.soft_failures),
                metrics=dict(rec.metrics),
            )
        else:
            # No metrics yet — neutral score (not a pass)
            gr = evaluate_all(None)
        scored.append((rank_key(gr), idea))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [idea for _, idea in scored[:top_n]]


def run_generation(
    *,
    ideas: list[Idea] | None = None,
    top_n: int = 3,
    mutants_per_parent: int = 2,
    use_grid: bool = True,
    seed: int = 42,
    registry: Registry | None = None,
    ideas_path: Path | None = None,
    render: bool = True,
) -> list[Idea]:
    """One evolution generation: select parents, mutate/grid, render, register.

    Does NOT run Quantiacs backtests — only creates strategy files and ledger
    entries with empty metrics placeholders.
    """
    rng = random.Random(seed)
    reg = registry or Registry()
    path = ideas_path or IDEAS_LEDGER

    pool = list(ideas) if ideas is not None else (load_ideas(path) or list(SEED_IDEAS))
    if not pool:
        pool = list(SEED_IDEAS)

    parents = select_parents(pool, reg, top_n=top_n)
    children: list[Idea] = []

    for parent in parents:
        for i in range(mutants_per_parent):
            child_rng = random.Random(rng.randint(0, 10**9) + i)
            children.append(mutate_idea(parent, rng=child_rng))
        if use_grid:
            children.extend(grid_variants(parent, max_variants=4))
        # Future: children.extend(expand_with_llm(parent, expander=...))

    # Dedup by id
    seen: set[str] = set()
    unique: list[Idea] = []
    for c in children:
        if c.id not in seen:
            seen.add(c.id)
            unique.append(c)

    # Persist ideas ledger (append new)
    existing = {i.id for i in load_ideas(path)}
    to_save = [i for i in unique if i.id not in existing]
    if to_save:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            import json

            for idea in to_save:
                f.write(json.dumps(idea.to_dict(), sort_keys=True) + "\n")

    for idea in unique:
        strat_path = ""
        if render:
            p = render_to_file(idea)
            strat_path = str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)
        rec = RunRecord(
            run_id=f"reg_{idea.id}",
            idea_id=idea.id,
            strategy_path=strat_path,
            params=dict(idea.params),
            desk_id=idea.desk_id,
            family=idea.family,
            generation=idea.generation,
            metrics={},  # placeholders — fill after real backtest
            hard_pass=None,
            soft_pass=None,
            status="registered",
            notes="Generated by evolve.run_generation; metrics pending real backtest.",
        )
        reg.append(rec)

    return unique
