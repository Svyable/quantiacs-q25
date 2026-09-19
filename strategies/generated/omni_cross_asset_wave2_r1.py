"""Pre-market implementation repair for preregistered OMNI wave 2.

The first wave-2 source contained a single invalid Python literal in evidence
metadata (`true` instead of `True`). No wave-2 market measurement or test run
occurred before this repair. The executed module below is byte-for-byte the
frozen source except for that literal correction; research formulas and
parameters are unchanged.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path


SOURCE = Path(__file__).with_name("omni_cross_asset_wave2.py")
text = SOURCE.read_text()
old = '"implemented_before_wave1_returns_observed":true if False else True,'
new = '"implemented_before_wave1_returns_observed":True,'
if text.count(old) != 1:
    raise RuntimeError("unexpected wave-2 source; refuse implicit repair")
text = text.replace(old, new)

BASE = types.ModuleType("omni_cross_asset_wave2_repaired")
BASE.__file__ = str(SOURCE)
sys.modules[BASE.__name__] = BASE
exec(compile(text, str(SOURCE), "exec"), BASE.__dict__)

_correlation_acceleration = BASE._correlation_acceleration
_vol_surface_curvature = BASE._vol_surface_curvature
_panel_disagreement = BASE._panel_disagreement
run = BASE.run


def main() -> None:
    BASE.main()


if __name__ == "__main__":
    main()
