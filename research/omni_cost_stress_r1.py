"""Pre-market import-path repair for research/omni_cost_stress.py.

The first exact-cost workflow failed while importing research.benchmark before
loading any market data. This wrapper only adds the repository root to
``sys.path`` and executes the frozen cost-stress script unchanged.
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

runpy.run_path(str(ROOT/"research"/"omni_cost_stress.py"),run_name="__main__")
