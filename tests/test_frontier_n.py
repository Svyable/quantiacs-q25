"""Frontier-N premeasurement mechanics and provenance tests; no economic claims."""
import json

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from research.benchmark import ROOT, check_causality, check_weights, load_module
from research.iteration import load_manifest
from research.preregister import sha256_file
from test_frontier_c import panel

CAMPAIGN = "frontier_20260912n"
FAMILY = "online_ar_surprise_persistence"
CENTRAL = 84
GRID = [63, 84, 126]


def module():
    return load_module(ROOT / f"strategies/generated/{CAMPAIGN}_{FAMILY}.py")


@pytest.mark.parametrize("mode", ("base", "ablation", "falsifier"))
def test_central_modes_are_causal_admissible_and_order_invariant(mode):
    data = panel(n=720)
    m = module()
    fn = lambda d: m.strategy(d, {"window": CENTRAL, "top_k": 5}, mode)
    weights = fn(data)
    assert check_causality(fn, data, weights)["status"] == "PASS"
    check_weights(weights, data)
    assert np.count_nonzero(weights.values) > 0
    assert float(weights.max()) <= 0.25 + 1e-12
    assert float(weights.sum("asset").max()) <= 1.0 + 1e-12

    shuffled = data.sel(asset=list(reversed(data.asset.values)))
    xr.testing.assert_allclose(fn(shuffled).sel(asset=data.asset), weights)


def test_destructive_controls_change_deployed_capital():
    data = panel(n=720)
    m = module()
    base = m.strategy(data, mode="base")
    ablation = m.strategy(data, mode="ablation")
    falsifier = m.strategy(data, mode="falsifier")
    assert float(abs(base - ablation).sum()) > 0.001
    assert float(abs(base - falsifier).sum()) > 0.001


@pytest.mark.parametrize("window", GRID)
def test_all_preregistered_base_windows_are_mechanically_valid(window):
    data = panel(n=720)
    m = module()
    fn = lambda d: m.strategy(d, {"window": window, "top_k": 5}, "base")
    weights = fn(data)
    check_weights(weights, data)
    assert check_causality(fn, data, weights)["status"] == "PASS"


def test_ineligibility_is_persistent_zero_until_next_rebalance():
    m = module()
    idx = pd.date_range("2026-01-05", periods=10, freq="D")
    score = pd.DataFrame({"A": 1.0, "B": 0.5}, index=idx)
    liquid = pd.DataFrame(True, index=idx, columns=score.columns)
    liquid.loc[idx[2], "A"] = False
    weights = m._allocate(score, liquid, idx, 2).to_pandas()
    assert weights.loc[idx[2], "A"] == 0.0
    assert weights.loc[idx[3], "A"] == 0.0
    assert weights.loc[idx[4], "A"] == 0.0
    assert weights.loc[idx[7], "A"] > 0.0


def test_campaign_contract_hash_and_spent_validation_boundary():
    dest = ROOT / "experiments" / CAMPAIGN
    manifest = load_manifest(dest / "manifest.json")
    assert len(manifest["candidates"]) == 5
    assert {row["family"] for row in manifest["candidates"]} == {FAMILY}
    assert set(manifest["controls"]) == {"equal_liquid", "inverse_vol_trend", "persistent_low_vol"}
    assert manifest["selection_folds"] == ["research", "dev"]
    assert manifest["automatic_promotion"] is False
    assert "forward_validation_2023_2024" in manifest["spent_validation_evidence"]

    prereg = dest / FAMILY / "preregistration.json"
    digest = sha256_file(prereg)
    assert digest == "a29d5e42055f5af420178bf6dd924453a48561bf25c349cfd68662b962d0b062"
    rows = manifest["candidates"]
    assert all(row["preregistration_sha256"] == digest for row in rows)
    assert digest in (ROOT / rows[0]["path"]).read_text()
    assert sorted({row["params"]["window"] for row in rows if row["mode"] == "base"}) == GRID

    freeze = json.loads((dest / "implementation_freeze.json").read_text())
    assert freeze["frozen_before_measurement"] is True
    assert freeze["market_returns_observed_before_freeze"] is False
    assert freeze["activation_type"] == "NEW_PREREGISTERED_FRONTIER"
    assert freeze["preregistration_sha256"][FAMILY] == digest

    slate = json.loads((dest / "idea_slate.json").read_text())
    assert slate["ideation_count"] == 10
    assert slate["implemented"] == FAMILY
    assert slate["performance_seen_before_score"] is False


def test_source_is_self_contained_and_declares_the_forecast_object():
    source = (ROOT / f"strategies/generated/{CAMPAIGN}_{FAMILY}.py").read_text()
    assert "online AR surprise persistence" in source
    assert "_online_ar1_surprise" in source
    assert "from research" not in source
    assert "from factory" not in source
