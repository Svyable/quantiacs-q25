"""Integrity checks for the promoted lattice-consensus Q25 submission."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_lattice_submission_is_exact_frozen_source_copy():
    assert (
        ROOT / "submissions/q25_lattice_consensus_multipass.py"
    ).read_bytes() == (
        ROOT / "strategies/generated/ebenezar_20260912_lattice_consensus.py"
    ).read_bytes()


def test_lattice_promotion_keeps_multipass_only_route():
    text = (ROOT / "evidence/deadline_20260918_lattice_consensus/promotion_receipt.json").read_text()
    assert '"single_pass_allowed": false' in text
    assert '"required_route": "365_DAY_QUANTIACS_MULTIPASS"' in text
