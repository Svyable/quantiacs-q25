"""Integrity test for the promoted Sharpe7 Q25 submission."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_sharpe7_submission_is_exact_frozen_source_copy():
    assert (
        ROOT / "submissions/q25_sharpe7_vol2_multipass.py"
    ).read_bytes() == (
        ROOT / "strategies/generated/ebenezar_20260912_sharpe7_vol2.py"
    ).read_bytes()
