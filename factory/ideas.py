"""Idea dataclass and seed library of concrete strategy ideas."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .desks import IdeaSpec, propose_all


@dataclass
class Idea:
    """Concrete, renderable strategy idea."""

    id: str
    name: str
    desk_id: str
    family: str
    thesis: str
    params: dict[str, Any]
    param_ranges: dict[str, tuple[float, float]]
    template_id: str = "strategy_multipass"
    tags: list[str] = field(default_factory=list)
    parent_id: str | None = None
    generation: int = 0

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # JSON-friendly ranges
        d["param_ranges"] = {k: list(v) for k, v in self.param_ranges.items()}
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Idea":
        ranges = {k: tuple(v) for k, v in d.get("param_ranges", {}).items()}
        return cls(
            id=d["id"],
            name=d["name"],
            desk_id=d["desk_id"],
            family=d["family"],
            thesis=d["thesis"],
            params=dict(d["params"]),
            param_ranges=ranges,
            template_id=d.get("template_id", "strategy_multipass"),
            tags=list(d.get("tags", [])),
            parent_id=d.get("parent_id"),
            generation=int(d.get("generation", 0)),
        )

    @classmethod
    def from_spec(cls, spec: IdeaSpec, idea_id: str | None = None) -> "Idea":
        iid = idea_id or f"{spec.desk_id}__{spec.name}"
        return cls(
            id=iid,
            name=spec.name,
            desk_id=spec.desk_id,
            family=spec.family,
            thesis=spec.thesis,
            params=dict(spec.params),
            param_ranges={k: tuple(v) for k, v in spec.param_ranges.items()},
            template_id=spec.template_id,
            tags=list(spec.tags),
        )


def build_seed_ideas() -> list[Idea]:
    """Materialize desk proposals into the seed Idea library."""
    ideas: list[Idea] = []
    for spec in propose_all():
        ideas.append(Idea.from_spec(spec))
    return ideas


SEED_IDEAS: list[Idea] = build_seed_ideas()


def save_ideas(ideas: list[Idea], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for idea in ideas:
            f.write(json.dumps(idea.to_dict(), sort_keys=True) + "\n")


def load_ideas(path: Path) -> list[Idea]:
    ideas: list[Idea] = []
    if not path.exists():
        return ideas
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            ideas.append(Idea.from_dict(json.loads(line)))
    return ideas
