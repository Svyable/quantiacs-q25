"""Reporting-only repair for omni_cross_asset_frontier_20260915r1.

Wave-1 economics were fully evaluated before the r1 process failed while
constructing its final evidence payload because the frozen source used the JSON
literal ``true`` in Python metadata. This wrapper does not alter any market
feature, forecast, weight, parameter, window, or evaluation. It only binds the
name ``true`` to Python ``True`` in the frozen module so the already-computed
payload can serialize on a clean rerun.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path


PATH = Path(__file__).with_name("omni_cross_asset_frontier_r1.py")
spec = importlib.util.spec_from_file_location("omni_frontier_r1_reporting", PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load repaired OMNI frontier implementation")
R1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R1)

# The NameError occurs only after every candidate has been evaluated, when the
# final evidence dictionary is constructed. Supplying this metadata-only name
# leaves all research functions and outputs unchanged.
R1.BASE.true = True

run = R1.run


def main() -> None:
    R1.main()


if __name__ == "__main__":
    main()
