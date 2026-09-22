import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "experiments/orthogonal_alpha_pack_2_20260922/vcb_hardening_preregistration.json"


def test_vcb_hardening_is_frozen_before_holdout():
    x = json.loads(P.read_text())
    assert x["strategy_id"] == "q25_volatility_contraction_breakout_v1"
    assert x["formula_changes_allowed"] is False
    assert x["parameter_changes_allowed"] is False
    assert x["holdout_access_allowed"] is False
    assert x["observed_selection"]["period"] == "2016-01-01/2022-12-31"
    assert x["observed_development"]["period"] == "2021-01-01/2022-12-31"
    assert x["observed_selection"]["sharpe_atr_cost"] == {"0.04": 1.926830, "0.08": 1.721545, "0.12": 1.514529}
    assert x["observed_development"]["sharpe_atr_cost"] == {"0.04": 1.231125, "0.08": 0.944528, "0.12": 0.656440}
    mechanics = set(x["required_mechanics"])
    assert {"bounded_replay_exact", "single_vs_multipass_parity", "determinism", "prefix_causality"} <= mechanics
    economics = set(x["required_economics"])
    assert {"benchmark_relative", "vol10_live_economics", "regime_stability", "incumbent_return_correlation"} <= economics
    assert "No parameter rescue" in x["advancement_rule"]
