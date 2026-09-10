"""Subprocess/import runner for strategy .py files.

Local Quantiacs research does not require a personal credential. The current
open-source toolbox special-cases ``API_KEY=default`` and uses it throughout its
own tests. This harness injects that value when no key is configured, *before*
anything imports ``qnt``.

A real participant API key is still required for account-bound services such as
participant-specific remote correlation/precheck/submission flows. Never commit
or print a real credential.
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
PUBLIC_API_KEY = "default"


@dataclass
class RunResult:
    ok: bool
    returncode: int
    stdout: str
    stderr: str
    strategy_path: str
    notes: str = ""


def load_dotenv(path: Path | None = None) -> None:
    """Load environment values from .env if present and not already set."""
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


def ensure_local_data_access() -> str:
    """Ensure qnt can import for local/public research and return the access mode key.

    The Quantiacs toolbox reads API_KEY at import time and exits on an empty
    value. Its source explicitly accepts the sentinel value ``default`` without
    account authentication. Therefore an absent/blank personal key is not a
    research blocker: inject ``default`` before importing qnt.
    """
    load_dotenv()
    key = os.environ.get("API_KEY", "").strip()
    if not key:
        key = PUBLIC_API_KEY
        os.environ["API_KEY"] = key
    return key


def require_api_key() -> str:
    """Backward-compatible alias for local research access.

    Historically this function raised when no personal API key was present.
    Keep the name so older harness code keeps working, but use public/default
    access instead of blocking research.
    """
    return ensure_local_data_access()


def has_authenticated_api_key() -> bool:
    """True only when a non-default participant credential is configured."""
    return ensure_local_data_access() != PUBLIC_API_KEY


def require_authenticated_api_key() -> str:
    """Return a participant credential or raise for account-bound operations."""
    key = ensure_local_data_access()
    if key == PUBLIC_API_KEY:
        raise RuntimeError(
            "This operation is account-bound and requires a real Quantiacs "
            "participant API key. Local/public market-data research and local "
            "stats should use API_KEY=default instead."
        )
    return key


def quantiacs_access_mode() -> str:
    """Return a safe provenance label without exposing the credential."""
    return "authenticated" if has_authenticated_api_key() else "public_default"


def _env_for_run(extra: dict[str, str] | None = None) -> dict[str, str]:
    ensure_local_data_access()
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
    """Run ``python path/to/strategy.py`` with public/default or authenticated access.

    Does not invent metrics — returns raw stdout/stderr.
    """
    ensure_local_data_access()
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
    ensure_local_data_access()
    path = Path(strategy_path).resolve()
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


def qnt_available() -> bool:
    """True if the Quantiacs toolbox appears importable."""
    ensure_local_data_access()
    try:
        import qnt.backtester  # noqa: F401

        return True
    except Exception:
        return False
