"""Subprocess/import runner for strategy .py files.

API_KEY is REQUIRED — empty/blank does NOT work (toolbox sys.exit).
Ensure API_KEY is set in the environment or project .env before running.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class RunResult:
    ok: bool
    returncode: int
    stdout: str
    stderr: str
    strategy_path: str
    notes: str = ""


def load_dotenv(path: Path | None = None) -> None:
    """Load API_KEY from .env if present and not already set (no extra deps)."""
    env_file = path or (ROOT / ".env")
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ and v:
            os.environ[k] = v


def require_api_key() -> None:
    """Fail clearly if API_KEY is missing/empty (blank does not enable free runs)."""
    load_dotenv()
    if not os.environ.get("API_KEY"):
        raise RuntimeError(
            "API_KEY is missing or empty. Create a free Quantiacs account, "
            "copy your profile key from https://quantiacs.com/personalpage/homepage, "
            "then export API_KEY=... or put it in .env (see .env.example)."
        )


def _env_for_run(extra: dict[str, str] | None = None) -> dict[str, str]:
    load_dotenv()
    env = dict(os.environ)
    if extra:
        env.update(extra)
    return env


def run_strategy_subprocess(
    strategy_path: str | Path,
    *,
    timeout: int | None = None,
    cwd: str | Path | None = None,
) -> RunResult:
    """Run ``python path/to/strategy.py`` with API_KEY from env/.env.

    Does not invent metrics — returns raw stdout/stderr.
    """
    require_api_key()
    path = Path(strategy_path).resolve()
    if not path.exists():
        return RunResult(
            ok=False,
            returncode=127,
            stdout="",
            stderr=f"Strategy not found: {path}",
            strategy_path=str(path),
            notes="missing file",
        )

    env = _env_for_run()
    try:
        proc = subprocess.run(
            [sys.executable, str(path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(cwd) if cwd else str(ROOT),
            env=env,
        )
        return RunResult(
            ok=proc.returncode == 0,
            returncode=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            strategy_path=str(path),
            notes="subprocess complete",
        )
    except subprocess.TimeoutExpired as e:
        return RunResult(
            ok=False,
            returncode=-1,
            stdout=(e.stdout or "") if isinstance(e.stdout, str) else "",
            stderr=f"Timeout after {timeout}s",
            strategy_path=str(path),
            notes="timeout",
        )


def load_strategy_module(strategy_path: str | Path) -> Any:
    """Import a strategy .py (executes module body; ``__main__`` block is skipped)."""
    require_api_key()
    path = Path(strategy_path).resolve()
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


def qnt_available() -> bool:
    """True if quantiacs toolbox appears importable."""
    try:
        import qnt.backtester  # noqa: F401

        return True
    except Exception:
        return False
