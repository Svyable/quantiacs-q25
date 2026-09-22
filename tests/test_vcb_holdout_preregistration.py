import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "experiments" / "vcb_holdout_20260922" / "preregistration.json"


def test_vcb_holdout_protocol_is_frozen_and_one_shot():
    x = json.loads(P.read_text())
    assert x["status"] == "PREREGISTERED_HOLDOUT_UNOPENED"
    assert x["evaluation"]["start"] == "2023-01-01"
    assert x["evaluation"]["one_shot"] is True
    assert x["cost_atr_percent"] == 4
    assert x["blend"] == {"vcb_weight": 0.5, "incumbent_weight": 0.5}
    assert x["frozen_before_holdout"] is True
    assert "holdout_retuning" in x["prohibited"]
    assert "post_hoc_grid_search" in x["prohibited"]
    assert x["advancement_gates"] == {
        "candidate_holdout_sharpe_gt_0": True,
        "candidate_holdout_vol10_normalized_return_gt_0": True,
        "candidate_full_2016_latest_sharpe_gt_1": True,
        "no_holdout_retuning": True,
    }
