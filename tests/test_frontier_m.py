"""Frontier-M reserve-activation mechanics and provenance tests; no economic claims."""
import json
import numpy as np
import pandas as pd
import pytest
import xarray as xr

from research.benchmark import ROOT, check_causality, check_weights, load_module
from research.iteration import load_manifest
from research.preregister import sha256_file
from test_frontier_c import panel

CAMPAIGN = "frontier_20260912m"
FAMILIES = ("volume_share_entropy_state", "dispersion_curvature", "entropy_disagreement_cash")
CENTRAL = {"dispersion_curvature": 42, "entropy_disagreement_cash": 84, "volume_share_entropy_state": 42}
GRIDS = {"dispersion_curvature": [21, 42, 63], "entropy_disagreement_cash": [63, 84, 126], "volume_share_entropy_state": [21, 42, 63]}
PRIOR = {"dispersion_curvature": "experiments/frontier_20260912l/dispersion_curvature/preregistration.json", "entropy_disagreement_cash": "experiments/frontier_20260912l/entropy_disagreement_cash/preregistration.json", "volume_share_entropy_state": "experiments/frontier_20260912l/volume_share_entropy_state/preregistration.json"}


def module(family):
    return load_module(ROOT / f"strategies/generated/{CAMPAIGN}_{family}.py")


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("mode", ("base", "ablation", "falsifier"))
def test_central_modes_are_causal_admissible_and_order_invariant(family, mode):
    data = panel(n=720)
    m = module(family)
    window = CENTRAL[family]
    fn = lambda d: m.strategy(d, {"window": window, "top_k": 5}, mode)
    weights = fn(data)
    assert check_causality(fn, data, weights)["status"] == "PASS"
    check_weights(weights, data)
    assert float(weights.max()) <= 0.25 + 1e-12
    assert float(weights.sum("asset").max()) <= 1.0 + 1e-12
    assert np.count_nonzero(weights.values) > 0
    shuffled = data.sel(asset=list(reversed(data.asset.values)))
    xr.testing.assert_allclose(fn(shuffled).sel(asset=data.asset), weights)


@pytest.mark.parametrize("family", FAMILIES)
def test_controls_change_deployed_capital(family):
    data = panel(n=720)
    m = module(family)
    base = m.strategy(data)
    ablation = m.strategy(data, mode="ablation")
    falsifier = m.strategy(data, mode="falsifier")
    assert float(abs(base - ablation).sum()) > 0.001
    assert float(abs(base - falsifier).sum()) > 0.001


@pytest.mark.parametrize("family", FAMILIES)
def test_ineligibility_is_persistent_zero_until_next_rebalance(family):
    m = module(family)
    idx = pd.date_range("2026-01-05", periods=10, freq="D")
    score = pd.DataFrame({"A": 1.0, "B": 0.5}, index=idx)
    liquid = pd.DataFrame(True, index=idx, columns=score.columns)
    liquid.loc[idx[2], "A"] = False
    weights = m._allocate(score, liquid, idx, 2).to_pandas()
    assert weights.loc[idx[2], "A"] == 0.0
    assert weights.loc[idx[3], "A"] == 0.0
    assert weights.loc[idx[4], "A"] == 0.0
    assert weights.loc[idx[7], "A"] > 0.0


def test_share_entropy_detects_concentration():
    m = module("volume_share_entropy_state")
    uniform = pd.Series([0.25, 0.25, 0.25, 0.25])
    concentrated = pd.Series([0.94, 0.02, 0.02, 0.02])
    assert m._share_entropy(concentrated) < m._share_entropy(uniform)


def test_dispersion_curvature_distinguishes_acceleration_from_first_difference():
    m = module("dispersion_curvature")
    d = pd.Series([10.0, 9.0, 7.0], index=pd.RangeIndex(3))
    recent, curvature = m._curvature_state(d, 1)
    assert recent.iloc[-1] == pytest.approx(2.0)
    assert curvature.iloc[-1] == pytest.approx(1.0)


def test_entropy_gate_is_high_vs_low_complement_with_ablation_always_on():
    m = module("entropy_disagreement_cash")
    prior = [0.1, 0.2, 0.3, 0.4]
    assert m._gate(0.5, prior, "base")
    assert not m._gate(0.5, prior, "falsifier")
    assert m._gate(0.5, prior, "ablation")
    assert not m._gate(0.05, prior, "base")
    assert m._gate(0.05, prior, "falsifier")


def test_activation_contract_hashes_and_spent_validation_boundary():
    dest = ROOT / "experiments" / CAMPAIGN
    manifest = load_manifest(dest / "manifest.json")
    assert len(manifest["candidates"]) == 15
    assert {row["family"] for row in manifest["candidates"]} == set(FAMILIES)
    assert set(manifest["controls"]) == {"equal_liquid", "inverse_vol_trend", "persistent_low_vol"}
    assert manifest["selection_folds"] == ["research", "dev"]
    assert manifest["automatic_promotion"] is False
    assert "forward_validation_2023_2024" in manifest["spent_validation_evidence"]

    freeze = json.loads((dest / "implementation_freeze.json").read_text())
    assert freeze["frozen_before_measurement"] is True
    assert freeze["market_returns_observed_before_freeze"] is False
    assert freeze["activation_type"] == "PREEXISTING_UNMEASURED_RESERVES"

    for family in FAMILIES:
        prereg = dest / family / "preregistration.json"
        digest = sha256_file(prereg)
        rows = [row for row in manifest["candidates"] if row["family"] == family]
        assert all(row["preregistration_sha256"] == digest for row in rows)
        assert freeze["preregistration_sha256"][family] == digest
        source = ROOT / rows[0]["path"]
        assert digest in source.read_text()
        assert freeze["source_sha256"][family] == sha256_file(source)
        prior = ROOT / PRIOR[family]
        assert freeze["prior_preregistration_sha256"][family] == sha256_file(prior)
        spec = json.loads(prereg.read_text())
        assert spec["status"] == "IMPLEMENTED_PENDING_EVIDENCE"
        assert spec["prior_preregistration"] == PRIOR[family]
        assert spec["validation"].startswith("2023-2024 is SPENT")
        assert sorted({row["params"]["window"] for row in rows if row["mode"] == "base"}) == GRIDS[family]
