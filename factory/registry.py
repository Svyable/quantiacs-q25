"""JSONL ledger of factory runs (path, params, metrics placeholders)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = ROOT / "results" / "registry.jsonl"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class RunRecord:
    """One factory / backtest run entry. Metrics may be null until a real run."""

    run_id: str
    idea_id: str
    strategy_path: str
    params: dict[str, Any]
    desk_id: str = ""
    family: str = ""
    generation: int = 0
    metrics: dict[str, Any] = field(default_factory=dict)
    hard_pass: bool | None = None
    soft_pass: bool | None = None
    hard_failures: list[str] = field(default_factory=list)
    soft_failures: list[str] = field(default_factory=list)
    status: str = "registered"  # registered | ran | failed | skipped
    created_at: str = field(default_factory=_utc_now)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Registry:
    """Append-only JSONL registry."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or DEFAULT_LEDGER
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: RunRecord) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict(), sort_keys=True) + "\n")

    def load(self) -> list[RunRecord]:
        if not self.path.exists():
            return []
        rows: list[RunRecord] = []
        with self.path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                rows.append(RunRecord(**d))
        return rows

    def latest_by_idea(self) -> dict[str, RunRecord]:
        out: dict[str, RunRecord] = {}
        for r in self.load():
            out[r.idea_id] = r
        return out
