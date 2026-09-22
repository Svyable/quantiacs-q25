import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "experiments" / "forced_union_20260922" / "preregistration.json"


def _load():
    return json.loads(PREREG.read_text())


def test_forced_union_mechanism_and_parameters_are_frozen():
    p = _load()
    assert p["status"] == "FROZEN_BEFORE_NEW_ECONOMIC_MEASUREMENT"
    assert p["mechanism"]["mode"] == "join_only"
    assert p["mechanism"]["parameter_changes"] == "none"
    assert p["mechanism"]["asset_selection"] == "automatic"
    assert p["mechanism"]["long_only"] is True
    assert p["frozen_parameters"] == {
        "fast_horizons": [7, 14, 12, 48, 30],
        "slow_horizons": [14, 28, 24, 96, 60],
        "pareto_max_dominators": 1,
        "score_power": 1.20,
        "score_shift_sd": 0.10,
        "vol_floor": 0.015,
        "smoothing_days": 3,
    }


def test_prior_join_observation_cannot_be_misrepresented_as_fresh_validation():
    p = _load()
    prior = p["prior_observation_disclosure"]
    assert prior["join_only_was_observed_as_control"] is True
    assert prior["selection_2016_2022_0p04_sharpe"] == 2.219388
    assert prior["development_2021_2022_0p04_sharpe"] == 0.804089
    assert prior["full_2016_plus_0p04_sharpe"] == 1.923528
    assert "not fresh evidence" in prior["note"]
    assert "No promotion" in prior["note"]


def test_chronology_cost_stress_and_destructive_controls_are_locked():
    p = _load()
    assert p["chronology"]["research"] == "2016-01-01/2020-12-31"
    assert p["chronology"]["development"] == "2021-01-01/2022-12-31"
    assert p["chronology"]["spent_validation_diagnostic"] == "2023-01-01/2024-12-31"
    assert p["chronology"]["untouched_live"] == "2026-10-01/2027-01-31"
    gates = p["advancement_gates"]
    assert gates["selection_2016_2022_sharpe_gt_1_costs"] == [0.04, 0.08, 0.12]
    assert gates["no_parameter_grid"] is True
    assert gates["no_retune_after_observation"] is True
    assert set(p["destructive_controls"]) == {
        "base_pareto", "root_only", "fast_only", "slow_only",
        "score_shuffle_with_selection_held_fixed",
    }
