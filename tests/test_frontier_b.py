"""Regression tests for frontier_20260910b (synthetic mechanics only; no economic evidence)."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
import pytest
import xarray as xr

from research.benchmark import ROOT, check_causality, check_weights, load_module
from research.iteration import load_manifest

CAMPAIGN = "frontier_20260910b"
FAMILIES = ("topology_migration", "liquidity_hysteresis", "shock_recovery_surface")


def panel(n=520, assets=8):
    rng = np.random.default_rng(20260910)
    shocks = rng.normal(0, 0.023, (n, assets))
    common = rng.normal(0.0003, 0.011, (n, 1))
    close = 100 * np.exp(np.cumsum(common + shocks, axis=0))
    opened = np.vstack([close[:1], close[:-1]]) * np.exp(rng.normal(0, .004, (n, assets)))
    high = np.maximum(close, opened) * (1 + rng.uniform(.003, .035, (n, assets)))
    low = np.minimum(close, opened) * (1 - rng.uniform(.003, .035, (n, assets)))
    vol = rng.lognormal(10, .75, (n, assets))
    liquid = np.ones((n, assets), dtype=float)
    liquid[:35, -1] = 0
    liquid[90:125, -1] = 0
    liquid[180:195, -1] = 0
    liquid[70:105, -2] = 0
    liquid[220:260, -2] = 0
    liquid[300:310, 0] = 0
    liquid[400:405, :] = 0
    fields = ["open", "high", "low", "close", "vol", "is_liquid"]
    return xr.DataArray(
        np.stack([opened, high, low, close, vol, liquid]),
        dims=("field", "time", "asset"),
        coords={
            "field": fields,
            "time": pd.date_range("2015-01-01", periods=n),
            "asset": [f"A{i}" for i in range(assets)],
        },
        name="cryptodaily",
    )


def module(family):
    return load_module(ROOT / f"strategies/generated/{CAMPAIGN}_{family}.py")


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("mode", ("base", "ablation", "falsifier"))
def test_causal_admissible_and_asset_order_invariant(family, mode):
    d = panel()
    m = module(family)
    fn = lambda x: m.strategy(x, mode=mode)
    w = fn(d)
    assert check_causality(fn, d, w)["status"] == "PASS"
    check_weights(w, d)
    assert np.count_nonzero(w.values) > 0
    assert float(w.max()) <= 0.25 + 1e-12
    assert float(w.sum("asset").max()) <= 1.0 + 1e-12
    shuffled = d.sel(asset=list(reversed(d.asset.values)))
    xr.testing.assert_allclose(fn(shuffled).sel(asset=d.asset), w)


@pytest.mark.parametrize("family", FAMILIES)
def test_controls_are_destructive_on_synthetic_panel(family):
    d = panel()
    m = module(family)
    base = m.strategy(d, mode="base")
    ablation = m.strategy(d, mode="ablation")
    falsifier = m.strategy(d, mode="falsifier")
    assert float(abs(base - ablation).sum()) > 0
    assert float(abs(base - falsifier).sum()) > 0


def test_campaign_contract_and_preregistration_hashes():
    directory = ROOT / "experiments" / CAMPAIGN
    slate = json.loads((directory / "idea_slate.json").read_text())
    assert len(slate) == 24
    assert len({x["area"] for x in slate}) == 3
    assert all(sum(x["scores"].values()) == x["priority_score"] for x in slate)
    assert all(x["performance_seen_before_score"] is False for x in slate)

    preregs = list(directory.glob("*/preregistration.json"))
    assert len(preregs) == 6
    for path in preregs:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        recorded = path.with_suffix(".sha256").read_text().strip()
        assert digest == recorded

    manifest = load_manifest(directory / "manifest.json")
    assert len(manifest["candidates"]) == 15
    assert set(manifest["controls"]) == {"equal_liquid", "inverse_vol_trend", "persistent_low_vol"}
    assert {x["family"] for x in manifest["candidates"]} == set(FAMILIES)
    assert manifest["automatic_promotion"] is False


@pytest.mark.parametrize("family", FAMILIES)
def test_source_identity_and_declared_grid(family):
    directory = ROOT / "experiments" / CAMPAIGN
    manifest = load_manifest(directory / "manifest.json")
    rows = [x for x in manifest["candidates"] if x["family"] == family]
    source = (ROOT / rows[0]["path"]).read_text()
    assert "PENDING RESEARCH STRATEGY" in source
    assert rows[0]["preregistration_sha256"] in source
    assert "from research" not in source
    assert "from factory" not in source
    d = panel()
    m = module(family)
    for row in rows:
        w = m.strategy(d, row["params"], row["mode"])
        check_weights(w, d)
