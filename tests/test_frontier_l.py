"""Frontier-L premeasurement mechanics and provenance tests; no economic claims."""
import json

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from research.benchmark import ROOT, check_causality, check_weights, load_module
from research.iteration import load_manifest
from research.preregister import sha256_file
from test_frontier_c import panel

CAMPAIGN = "frontier_20260912l"
FAMILIES = (
    "permutation_entropy_contraction",
    "dollar_volume_share_migration",
    "relative_value_convergence",
)
CENTRAL = {
    "permutation_entropy_contraction": 84,
    "dollar_volume_share_migration": 42,
    "relative_value_convergence": 42,
}
GRIDS = {
    "permutation_entropy_contraction": [63, 84, 126],
    "dollar_volume_share_migration": [21, 42, 63],
    "relative_value_convergence": [21, 42, 63],
}


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


def test_entropy_is_low_for_repeating_pattern_and_high_for_mixed_sequence():
    m = module("permutation_entropy_contraction")
    repeating = np.tile([0.0, 1.0, 2.0], 30)
    rng = np.random.default_rng(7)
    mixed = rng.normal(size=90)
    assert m._ordinal_entropy(repeating) < m._ordinal_entropy(mixed)


def test_volume_share_uses_eligible_universe_only():
    data = panel(n=720)
    m = module("dollar_volume_share_migration")
    base = m.strategy(data)
    absent = xr.full_like(data.isel(asset=[0]), np.nan).assign_coords(asset=["FUTURE"])
    absent.loc[dict(field="is_liquid")] = 0
    expanded = xr.concat([data, absent], dim="asset")
    xr.testing.assert_allclose(m.strategy(expanded).sel(asset=data.asset), base)


def test_relative_value_falsifier_is_opposite_dispersion_state():
    m = module("relative_value_convergence")
    data = panel(n=720)
    base = m.strategy(data)
    falsifier = m.strategy(data, mode="falsifier")
    assert float(abs(base - falsifier).sum()) > 1.0


def test_campaign_contract_hashes_and_spent_validation_boundary():
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
    assert freeze["activation_type"] == "NEW_PREREGISTERED_FRONTIER"
    slate = json.loads((dest / "idea_slate.json").read_text())
    assert slate["ideation_count"] == 24
    assert slate["preregister_count"] == 6
    assert slate["implement_count"] == 3

    for family in FAMILIES:
        prereg = dest / family / "preregistration.json"
        digest = sha256_file(prereg)
        rows = [row for row in manifest["candidates"] if row["family"] == family]
        assert all(row["preregistration_sha256"] == digest for row in rows)
        assert freeze["preregistration_sha256"][family] == digest
        assert digest in (ROOT / rows[0]["path"]).read_text()
        spec = json.loads(prereg.read_text())
        assert spec["status"] == "IMPLEMENTED_PENDING_EVIDENCE"
        assert spec["validation"].startswith("2023-2024 is SPENT")
        assert sorted({row["params"]["window"] for row in rows if row["mode"] == "base"}) == GRIDS[family]

    reserves = ["volume_share_entropy_state", "dispersion_curvature", "entropy_disagreement_cash"]
    for family in reserves:
        prereg = dest / family / "preregistration.json"
        assert sha256_file(prereg) == freeze["reserve_preregistration_sha256"][family]
        assert json.loads(prereg.read_text())["status"] == "PREREGISTERED_NOT_IMPLEMENTED"
