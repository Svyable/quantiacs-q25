"""Reject malformed JSON and duplicate object keys in canonical repo evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


class DuplicateKeyError(ValueError):
    pass


def _unique_object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise DuplicateKeyError(f"duplicate JSON key: {key!r}")
        out[key] = value
    return out


def validate_json(path: Path) -> None:
    json.loads(path.read_text(), object_pairs_hook=_unique_object)


def json_files(paths: list[Path]):
    seen = set()
    for path in paths:
        candidates = path.rglob("*.json") if path.is_dir() else [path]
        for candidate in candidates:
            if candidate.suffix != ".json" or not candidate.is_file():
                continue
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            yield candidate


def scan(paths: list[Path]) -> list[tuple[Path, str]]:
    failures = []
    for path in sorted(json_files(paths)):
        try:
            validate_json(path)
        except (json.JSONDecodeError, DuplicateKeyError) as exc:
            failures.append((path, str(exc)))
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    failures = scan(args.paths)
    if failures:
        for path, error in failures:
            print(f"{path}: {error}")
        return 1
    checked = sum(1 for _ in json_files(args.paths))
    print(f"JSON integrity OK: {checked} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
