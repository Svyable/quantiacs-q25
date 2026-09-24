"""Frozen 5% sparse-trigger measurement entry point.

This deliberately reuses the audited turnover evaluator machinery while swapping only
the preregistered execution operator and evidence field names in a follow-up commit.
"""
from research.measure_turnover_ensemble import main

if __name__ == "__main__":
    main()
