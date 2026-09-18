"""Submission artifact must reproduce the measured hit126 implementation exactly."""
import importlib.util
from pathlib import Path
import xarray as xr
from tests.test_q25_deadline_hit126_consistency import panel
from strategies.generated import q25_deadline_hit126_consistency as measured

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"submissions"/"q25_hit126_consistency_singlepass.py"

def _load_submission():
    spec=importlib.util.spec_from_file_location("q25_hit126_submission",PATH)
    assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_submission_matches_measured_source_weights():
    data=panel()
    submission=_load_submission()
    expected=measured.compute_weights(data)
    got=submission.compute_weights(data)
    xr.testing.assert_allclose(expected,got)
    assert submission.HIT_WINDOW==measured.HIT_WINDOW
    assert submission.TOP_K==measured.TOP_K
    assert submission.NAME_CAP==measured.NAME_CAP
