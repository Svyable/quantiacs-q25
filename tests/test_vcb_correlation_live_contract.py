import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "experiments/vcb_correlation_live_20260922/preregistration.json"


def test_vcb_correlation_live_contract_is_fail_closed():
    p = json.loads(PATH.read_text())
    assert p["status"] == "PREREGISTERED_UNMEASURED"
    assert p["candidate"] == "q25_volatility_contraction_breakout_v1"
    assert p["incumbent"] == "q25_deadline_hit126_consistency_v1"
    assert p["strategy_changes_allowed"] is False
    assert p["parameter_changes_allowed"] is False
    assert p["holdout_2023_plus_access_allowed"] is False
    assert p["measurement_end"] == "2022-12-31"
    assert p["cost_atr_percent"] == 4
    gates = p["advancement_gates"]
    assert gates == {
        "vcb_full_2016_2022_sharpe_gt": 1.0,
        "vcb_development_2021_2022_sharpe_gt": 0.0,
        "absolute_development_return_correlation_lt": 0.8,
        "candidate_10pct_vol_normalized_return_gt": 0.0,
        "no_holdout_loaded": True,
    }
    required = {
        "daily_return_pearson_correlation_full_2016_2022",
        "daily_return_pearson_correlation_development_2021_2022",
        "candidate_10pct_vol_normalized_return",
        "incumbent_10pct_vol_normalized_return",
        "equal_weight_blend_10pct_vol_normalized_return",
        "equal_weight_blend_sharpe",
    }
    assert required <= set(p["measurements"])
