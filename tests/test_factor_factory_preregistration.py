import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "experiments" / "factor_factory_20260922" / "preregistration.json"


def test_factor_factory_is_frozen_and_fail_closed():
    p = json.loads(P.read_text())
    assert p["status"] == "PREREGISTERED"
    assert p["data"] == "Quantiacs/Sponsor crypto_daily_long only"
    assert p["universe"] == "automatic top-10 monthly liquid universe"
    assert p["chronology"]["research"] == ["2016-01-01", "2020-12-31"]
    assert p["chronology"]["development"] == ["2021-01-01", "2022-12-31"]
    assert p["chronology"]["holdout"][1] == "UNOPENED_FOR_THIS_EXPERIMENT"
    assert p["official_cost_atr_percent"] == 4
    assert p["cost_sensitivity_atr_percent"] == [4, 8, 12]
    assert len(p["families"]) == 4
    assert p["common_portfolio_rules"]["long_only"] is True
    assert p["common_portfolio_rules"]["name_cap"] == 0.25
    assert p["common_portfolio_rules"]["gross_weight_lte"] == 1.0
    g = p["advancement_gates"]
    assert g["selection_2016_2022_sharpe_4pct_gt"] == 1.0
    assert g["development_abs_return_correlation_to_vcb_lt"] == 0.8
    assert g["incremental_50_50_blend_development_sharpe_gt_both_components"] is True
    assert "cross-sectional score identity permutation" in p["required_controls"]
    assert "2023+ access during discovery" in p["forbidden"]
    assert "parameter grids" in p["forbidden"]
    assert "post-hoc rescue" in p["forbidden"]
