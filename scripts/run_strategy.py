#!/usr/bin/env python3
"""Run a Quantiacs strategy module.

No personal Quantiacs credential is required for local/public-data research.
When API_KEY is absent, the repo harness injects ``API_KEY=default`` before qnt
imports. Set a real participant key only when an account-bound service needs it.

Usage:
  python scripts/run_strategy.py strategies/baseline_sma_rsi.py
  API_KEY=default python scripts/run_strategy.py strategies/baseline_sma_rsi.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from factory.runner import ensure_local_data_access, quantiacs_access_mode, run_strategy_subprocess, qnt_available


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a Q25 strategy .py via subprocess")
    parser.add_argument("strategy", type=str, help="Path to strategy .py")
    parser.add_argument("--timeout", type=int, default=None, help="Optional timeout seconds")
    args = parser.parse_args()

    ensure_local_data_access()
    print(f"Quantiacs access mode: {quantiacs_access_mode()}", file=sys.stderr)

    if not qnt_available():
        print(
            "WARNING: qnt toolbox not importable in this environment. "
            "Install via: pip install 'git+https://github.com/quantiacs/toolbox.git' "
            "or conda install -c quantiacs-source qnt",
            file=sys.stderr,
        )

    path = Path(args.strategy)
    if not path.is_absolute():
        path = (ROOT / path).resolve()

    result = run_strategy_subprocess(path, timeout=args.timeout)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return 0 if result.ok else result.returncode or 1


if __name__ == "__main__":
    raise SystemExit(main())
