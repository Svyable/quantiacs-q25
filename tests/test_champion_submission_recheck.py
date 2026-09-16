from __future__ import annotations

from research import champion_submission_recheck as mod


def test_selector_adapters_change_only_two_frozen_selector_lines():
    original = mod.C165_PATH.read_text().splitlines()
    for candidate in ("CoCrash126", "Trend_hit126"):
        adapted = mod._selector_adapter_source(candidate).splitlines()
        differences = [(a, b) for a, b in zip(original, adapted) if a != b]
        assert len(original) == len(adapted)
        assert len(differences) == 2
        assert differences[0][0] == "CANDIDATE_ID = 'C165'"
        assert differences[0][1] == f"CANDIDATE_ID = {candidate!r}"
        assert differences[1][0] == "    CANDIDATE = 'C165'"
        assert differences[1][1] == f"    CANDIDATE = {candidate!r}"


def test_candidate_provenance_is_explicit_and_not_overclaimed():
    c165, p165 = mod.load_candidate_module("C165")
    v12, p12 = mod.load_candidate_module("V12")
    assert c165.CANDIDATE_ID == "C165"
    assert v12.CANDIDATE_ID == "V12"
    assert p165["provenance_class"] == "EXACT_COMMITTED_MIRROR"
    assert p12["provenance_class"] == "EXACT_COMMITTED_MIRROR"

    for candidate in ("CoCrash126", "Trend_hit126"):
        loaded, provenance = mod.load_candidate_module(candidate)
        assert loaded.CANDIDATE_ID == candidate
        assert provenance["provenance_class"] == "SELECTOR_ONLY_ADAPTER_FROM_C165_BUNDLE"
        assert provenance["selector_only_adapter"] is True
        assert provenance["formula_changed"] is False
        assert provenance["parameter_changed"] is False
        assert provenance["byte_identical_historical_artifact_claimed"] is False


def test_selection_policy_uses_only_research_and_dev_folds():
    folds = mod._folds("2026-09-16")
    assert [row["id"] for row in folds] == ["research", "dev", "validation", "diagnostic"]
    assert folds[0]["end"] == "2020-12-31"
    assert folds[1]["end"] == "2022-12-31"
    assert folds[2]["end"] == "2024-12-31"
    assert folds[3]["start"] == "2025-01-01"
    assert folds[3]["end"] == "2026-09-16"
