import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "experiments" / "breadth_dispersion_holdout_20260923" / "preregistration.json"


def test_breadth_dispersion_holdout_is_fail_closed():
    p = json.loads(P.read_text())
    assert p["status"] == "PREREGISTERED"
    assert p["candidate"] == "breadth_dispersion"
    assert p["mechanism_frozen"] is True
    assert p["parameters_frozen"] is True
    assert p["selection_history_end"] == "2022-12-31"
    assert p["holdout_start"] == "2023-01-01"
    assert p["cost_atr_percent"] == 4
    assert p["stress_cost_atr_percent"] == [8, 12]
    assert p["blend_weight_candidate"] == 0.5
    assert p["blend_weight_vcb"] == 0.5
    gates = p["advancement_gates"]
    assert gates["standalone_holdout_sharpe_gt"] == 0.0
    assert gates["standalone_holdout_12pct_cost_sharpe_gt"] == 0.0
    assert gates["holdout_abs_return_correlation_to_vcb_lt"] == 0.8
    assert gates["frozen_50_50_blend_holdout_sharpe_gt_each_component"] is True
    assert gates["no_post_holdout_retuning"] is True
    assert "post-hoc grids" in p["forbidden"]
    assert "parameter changes" in p["forbidden"]
