"""HELIOS mechanics: labels, risk budgets, execution, and 365-day replay.

Synthetic returns test implementation health only, never economic quality.
"""
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from research.benchmark import ROOT, check_causality, check_weights, load_module
from research.iteration import load_manifest
from test_frontier_c import panel

PATH = ROOT / "strategies/generated/q25_helios_causal.py"
CAMPAIGN = ROOT / "experiments/helios_20260914"
M = load_module(PATH)
MANIFEST = load_manifest(CAMPAIGN / "manifest.json")


@pytest.mark.parametrize("job", MANIFEST["candidates"], ids=lambda j: j["id"])
def test_all_frozen_cells_prefix_replay_and_asset_order(job):
    data = panel(n=710)
    fn = lambda d: M.strategy(d, job["params"], job["mode"])
    weights = fn(data)
    assert check_causality(fn, data, weights, checkpoints=5)["status"] == "PASS"
    assert (weights.values > 0).any()
    xr.testing.assert_allclose(fn(data.sel(asset=data.asset.values[::-1])).sel(asset=data.asset), weights)


@pytest.mark.parametrize("mode", ("base", "falsifier"))
def test_inactive_future_asset_does_not_change_history(mode):
    data = panel(n=510)
    absent = xr.full_like(data.isel(asset=[0]), np.nan).assign_coords(asset=["FUTURE"])
    absent.loc[dict(field="is_liquid")] = 0
    got = M.strategy(xr.concat([data, absent], dim="asset"), mode=mode)
    xr.testing.assert_allclose(got.sel(asset=data.asset), M.strategy(data, mode=mode))
    assert not got.sel(asset="FUTURE").values.any()


def test_completed_labels_nonoverlap_no_survivor_mask():
    times = pd.date_range("2020-01-01", periods=80)
    close = pd.DataFrame(np.exp(np.arange(80)[:, None] * np.array([.01, .02, .03])), index=times)
    factor = pd.DataFrame(np.tile([-1., 0., 1.], (80, 1)), index=times)
    mask = close.notna()
    # A source-eligible asset leaving the universe during its outcome window
    # must still contribute to a realized training label.
    mask.iloc[20:, 0] = False
    ic = M._completed_ic(factor, close, mask, 5)
    assert (np.diff(ic.dropna().index.values) == np.timedelta64(5, "D")).all()
    assert ic.iloc[20:25].notna().any()
    np.testing.assert_allclose(ic.dropna(), 1, atol=1e-12)
    altered = close.copy()
    altered.iloc[24:] *= np.array([3., 2., 1.])
    pd.testing.assert_series_equal(M._completed_ic(factor, altered, mask, 5).iloc[:24], ic.iloc[:24])
    missing = close.copy()
    missing.iloc[18:25, 0] = np.nan
    assert M._completed_ic(factor, missing, mask, 5).iloc[20:25].isna().all()


def test_current_outcome_cannot_update_current_coefficients():
    data = panel(n=510)
    before = M._factor_weights(M._context(data), 126)
    altered = data.copy(deep=True)
    altered.loc[dict(field="close", time=altered.time[-1])] *= np.linspace(.7, 1.3, 8)
    after = M._factor_weights(M._context(altered), 126)
    pd.testing.assert_frame_equal(after, before)
    assert not np.allclose(before.iloc[-1], .25)
    np.testing.assert_allclose(before.sum(axis=1), 1)
    assert before.min().min() >= .65 / 4


def test_covariance_psd_and_risk_contributions():
    rng = np.random.default_rng(21)
    market = rng.normal(0, .02, 63)
    r = market[:, None] * np.array([.5, 1., 2.]) + rng.normal(0, .01, (63, 3))
    covariance = M._covariance(r, market)
    assert np.linalg.eigvalsh(covariance).min() > 0
    budget = np.array([.2, .3, .5])
    weights = M._risk_budget(covariance, budget)
    contributions = weights * (covariance @ weights)
    np.testing.assert_allclose(contributions / contributions.sum(), budget, atol=1e-8)
    diagonal = M._covariance(r, market, diagonal=True)
    expected = np.sqrt(budget / np.diag(diagonal))
    np.testing.assert_allclose(M._risk_budget(diagonal, budget), expected / expected.sum(), atol=1e-10)
    # Perfectly collinear observations still have a finite positive risk floor.
    assert np.linalg.eigvalsh(M._covariance(np.tile(market[:, None], (1, 3)), market)).min() > 0


def test_weekly_exit_cannot_resurrect_and_risk_cannot_expand():
    dates = pd.date_range("2020-01-06", periods=9)  # Monday
    desired = pd.DataFrame(.25, index=dates, columns=["A", "B"])
    eligible = desired.notna()
    eligible.iloc[2, 0] = False
    ceiling = pd.Series(.5, index=dates)
    ceiling.iloc[4] = .1
    held = M._weekly_targets(desired, eligible, ceiling)
    assert not held.A.iloc[2:7].any()
    np.testing.assert_allclose(held.sum(axis=1).iloc[4:7], .1)
    assert held.A.iloc[7] == .25
    # Starting replay midweek does not invent an unseen Monday target.
    assert not M._weekly_targets(desired.iloc[1:], eligible.iloc[1:], ceiling.iloc[1:]).iloc[:6].values.any()


def test_controls_survive_portfolio_construction():
    data = panel(n=710)
    base = M.strategy(data)
    for job in MANIFEST["candidates"][3:]:
        got = M.strategy(data, job["params"], job["mode"])
        assert float(abs(base - got).sum()) > .001, job["id"]


def test_missing_data_flat_market_and_input_failures():
    data = panel(n=400)
    data.loc[dict(field="is_liquid", time=data.time[-3:])] = np.nan
    weights = M.strategy(data)
    check_weights(weights, data)
    assert not weights.isel(time=slice(-3, None)).values.any()
    flat = panel(n=400)
    for f in ("open", "close"):
        flat.loc[dict(field=f)] = 100
    flat.loc[dict(field="high")] = 101
    flat.loc[dict(field="low")] = 99
    assert not M.strategy(flat).values.any()
    for n in (0, 1, 20, 125):
        short = flat.isel(time=slice(0, n))
        assert not M.strategy(short).values.any()
    with pytest.raises(ValueError, match="contiguous"):
        M.strategy(data.isel(time=list(range(30)) + list(range(31, 400))))
    with pytest.raises(ValueError, match="frozen"):
        M.strategy(data, dict(window=200))
    with pytest.raises(ValueError, match="missing"):
        M.strategy(data.sel(field=["close"]))


def test_single_file_import_outside_repository(tmp_path):
    copied = tmp_path / "strategy.py"
    copied.write_bytes(PATH.read_bytes())
    result = subprocess.run([sys.executable, str(copied), "--help"], cwd=tmp_path,
                            capture_output=True, text=True, check=True)
    assert "--write" in result.stdout
    subprocess.run([sys.executable, "-c",
                    "import runpy, sys; runpy.run_path('strategy.py', run_name='candidate'); "
                    "assert 'qnt' not in sys.modules"], cwd=tmp_path, check=True)


def test_preregistration_budget_and_controls():
    assert len(MANIFEST["candidates"]) == 7
    assert sum(j["mode"] == "base" for j in MANIFEST["candidates"]) == 3
    assert all(j["parent_id"] == "helios_w126" for j in MANIFEST["candidates"][3:])
    spec = json.loads((CAMPAIGN / "factor_learning/preregistration.json").read_text())
    assert spec["classification"] == "user_directed_family_refinement"


def test_observed_packets_match_frozen_code_and_reject_failed_controls():
    from research.preregister import sha256_file
    freeze = json.loads((CAMPAIGN / "implementation_freeze.json").read_text())
    assert all(sha256_file(ROOT / path) == value for path, value in freeze["sha256"].items())
    evidence = ROOT / "evidence/helios_20260914"
    context = json.loads((evidence / "context.json").read_text())
    assert context["manifest_sha256"] == sha256_file(CAMPAIGN / "manifest.json")
    for job in MANIFEST["candidates"]:
        row = json.loads((evidence / "candidate_packets" / (job["id"] + ".json")).read_text())
        assert row["data_sha256"] == context["data_sha256"]
        assert row["strategy_source_sha256"] == sha256_file(PATH)
        assert row["preregistration_sha256"] == job["preregistration_sha256"]
        assert row["params"] == job["params"]
        assert row["status"] == "COMPLETE"
    matrix = json.loads((evidence / "matrix.json").read_text())
    assert len(matrix["candidates"]) == 10
    assert matrix["families"][0]["decision_code"] == "FALSIFIED_DEVELOPMENT"
    assert set(matrix["families"][0]["failed_controls"]) == {"helios_misassigned_skill", "helios_no_cost_gate"}
