import json
from pathlib import Path

from scripts.build_submission_readiness import render

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data" / "submission_readiness.json"
MARKDOWN = ROOT / "docs" / "SUBMISSION_READINESS.md"


def test_submission_readiness_artifacts_are_current():
    payload, markdown = render()
    assert json.loads(DATA.read_text()) == payload
    assert MARKDOWN.read_text() == markdown


def test_public_smoke_never_becomes_account_clearance_for_participant_zero():
    payload, _ = render()
    for row in payload["candidates"]:
        smoke = row["public_correlation_smoke"]
        if smoke.get("participant_id") == "0":
            assert smoke["account_bound_clearance"] is False
            assert "ACCOUNT_BOUND_UNIQUENESS_CORRELATION" in row["blockers"] or not row["artifact_present"]


def test_exact_artifacts_are_not_inferred():
    payload, _ = render()
    for row in payload["candidates"]:
        path = ROOT / row["production_artifact"]
        assert row["artifact_present"] == path.exists()


def test_full_history_floor_is_a_boolean_measurement_not_a_rank():
    payload, _ = render()
    assert payload["policy"]["strategy_ranking"] == "FORBIDDEN_ON_THIS_SURFACE"
    for row in payload["candidates"]:
        metric = row["full_history"]["contest_floor_4pct_pass"]
        assert metric in {True, False, None}


def test_sharpe7_forward_receipt_is_frozen_and_formula_immutable():
    payload, _ = render()
    row = next(r for r in payload["candidates"] if r["id"] == "ebenezar_20260912_sharpe7_vol2")
    forward = row["forward_validation"]
    assert forward["state"] == "FROZEN_FORWARD_OBSERVED"
    assert forward["validation_window"] == ["2023-01-01", "2024-12-31"]
    assert forward["pass_4pct"] is True
    assert forward["pass_10pct"] is True
    assert row["stage"] == "PROMOTED_FORWARD_PASS_PENDING_ACCOUNT_BOUND_CORRELATION"


def test_missing_forward_evidence_stays_missing():
    payload, _ = render()
    row = next(r for r in payload["candidates"] if r["id"] == "q25_sota_meta_ensemble_v1")
    assert row["forward_validation"]["state"] == "NOT_MEASURED"
    assert row["forward_validation"]["sharpe_4pct_atr"] is None
    assert "FROZEN_FORWARD_CONFIDENCE_NOT_MEASURED" in row["blockers"]
