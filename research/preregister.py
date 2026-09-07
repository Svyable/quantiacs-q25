"""Write preregistration.json and SHA256 hash (L8 hygiene)."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Union


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Union[str, Path]) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_preregistration(
    dest_dir: Union[str, Path],
    payload: Mapping[str, Any],
    *,
    filename: str = "preregistration.json",
) -> tuple[Path, str]:
    """Write JSON (sorted keys, stable indent) and return (path, sha256)."""
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / filename
    data = dict(payload)
    if not data.get("created_utc"):
        data["created_utc"] = utc_now_iso()
    text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    path.write_text(text, encoding="utf-8")
    digest = sha256_file(path)
    hash_path = dest_dir / "preregistration.sha256"
    hash_path.write_text(f"{digest}  {filename}\n", encoding="utf-8")
    return path, digest


def load_template(repo_root: Optional[Path] = None) -> dict:
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[1]
    tpl = repo_root / "templates" / "preregistration.json"
    return json.loads(tpl.read_text(encoding="utf-8"))


if __name__ == "__main__":
    # Smoke: write to a temp experiments path if args given
    root = Path(__file__).resolve().parents[1]
    out = root / "experiments" / "_prereg_smoke"
    tpl = load_template(root)
    tpl["experiment_id"] = "_prereg_smoke"
    tpl["track"] = "robustness"
    tpl["mechanism"] = "momentum"
    tpl["thesis"] = "smoke test — delete me"
    tpl["falsifier"] = "n/a"
    path, digest = write_preregistration(out, tpl)
    print(path)
    print(digest)
