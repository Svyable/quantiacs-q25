"""Integrity test for the promoted SOTA meta Q25 submission."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_sota_submission_is_exact_frozen_source_copy():
    assert (
        ROOT / "submissions/q25_sota_meta_ensemble_multipass.py"
    ).read_bytes() == (
        ROOT / "strategies/q25_sota_meta_ensemble.py"
    ).read_bytes()
