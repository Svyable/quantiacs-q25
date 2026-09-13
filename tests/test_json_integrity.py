from pathlib import Path

import pytest

from scripts.check_json_integrity import DuplicateKeyError, scan, validate_json


ROOT = Path(__file__).resolve().parents[1]


def test_duplicate_json_keys_are_rejected(tmp_path):
    path = tmp_path / "duplicate.json"
    path.write_text('{"decision":"KEEP","decision":"KILL"}\n')
    with pytest.raises(DuplicateKeyError, match="decision"):
        validate_json(path)


def test_canonical_evidence_and_experiment_json_is_strict():
    failures = scan([ROOT / "evidence", ROOT / "experiments", ROOT / "docs" / "data"])
    assert failures == []
