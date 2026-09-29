import importlib.util
from pathlib import Path
import numpy as np
import xarray as xr

from strategies.generated import q25_factor_factory as ff
from strategies.generated import q25_volatility_contraction_breakout as vcb
from research.benchmark import check_causality

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = "submissions/q25_vcb_breadth_ensemble_singlepass.py"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / ADAPTER)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def _data(seed=11, n=420, assets=("a", "b", "c", "d", "e", "f")):
    rng = np.random.default_rng(seed)
    t = np.arange(np.datetime64("2020-01-01"), np.datetime64("2020-01-01") + np.timedelta64(n, "D"))
    close = 100 * np.exp(np.cumsum(rng.normal(.001, .03, (n, len(assets))), axis=0))
    liq = (rng.random((n, len(assets))) > .1).astype(float)
    return xr.DataArray(np.stack([close, liq]), dims=("field", "time", "asset"),
                        coords={"field": ["close", "is_liquid"], "time": t, "asset": list(assets)})


def test_members_exactly_match_frozen_research_sources():
    adapter = _load("ens_members"); d = _data()
    np.testing.assert_array_equal(adapter.vcb_weights(d).values, vcb.calculate_weights(d).values)
    np.testing.assert_array_equal(adapter.breadth_dispersion_weights(d).values,
                                  ff.FACTORS["breadth_dispersion_interaction"](d).values)


def test_blend_exactly_matches_measured_static_ensemble():
    adapter = _load("ens_blend"); d = _data()
    research = .5 * ff.FACTORS["breadth_dispersion_interaction"](d) + .5 * vcb.calculate_weights(d)
    got = adapter.calculate_weights(d)
    assert got.dims == ("time", "asset")
    np.testing.assert_array_equal(got.values, research.transpose("time", "asset").values)


def test_long_only_liquid_caps_and_gross():
    adapter = _load("ens_caps"); d = _data()
    d.loc[dict(field="is_liquid", asset="a", time=d.time.values[-30:])] = 0
    w = adapter.calculate_weights(d)
    assert float(w.min()) >= 0
    assert float(w.max()) <= .25 + 1e-12
    assert float(w.sum("asset").max()) <= 1 + 1e-12
    assert float(w.sel(asset="a", time=d.time.values[-30:]).max()) == 0
    liq = d.sel(field="is_liquid").transpose("time", "asset").values
    assert not ((w.values > 0) & (liq != 1)).any()


def test_prefix_causality_bounded_replay_and_asset_order():
    adapter = _load("ens_causal"); d = _data()
    assert check_causality(adapter.calculate_weights, d)["status"] == "PASS"
    w = adapter.calculate_weights(d)
    rev = d.sel(asset=list(reversed(d.asset.values)))
    wr = adapter.calculate_weights(rev).sel(asset=d.asset.values)
    assert float(abs(w - wr).max()) <= 1e-12
    xr.testing.assert_identical(w, adapter.calculate_weights(d))


def _zero_price_data():
    d = _data(seed=5, n=900)
    d.loc[dict(field="close", asset="c", time=d.time.values[300:305])] = 0.0
    d.loc[dict(field="is_liquid", asset="c", time=d.time.values[300:305])] = 0.0
    return d


def test_zero_close_is_backend_invariant_and_causal():
    adapter = _load("ens_zero"); d = _zero_price_data()
    default = adapter.calculate_weights(d)
    with xr.set_options(use_bottleneck=False):
        native = adapter.calculate_weights(d)
    assert float(abs(default - native).max()) <= 1e-10
    assert check_causality(adapter.calculate_weights, d, full=default)["status"] == "PASS"


def test_frozen_research_members_diverge_across_backends_on_zero_close():
    # Documents the defect the adapter hardens: an infinite return poisons
    # bottleneck's running-sum rolling kernels long after the event.
    d = _zero_price_data()
    default = .5 * ff.FACTORS["breadth_dispersion_interaction"](d) + .5 * vcb.calculate_weights(d)
    with xr.set_options(use_bottleneck=False):
        native = .5 * ff.FACTORS["breadth_dispersion_interaction"](d) + .5 * vcb.calculate_weights(d)
    assert float(abs(default - native).max()) > 1e-3


def test_strategy_returns_latest_row_only():
    adapter = _load("ens_last"); d = _data()
    last = adapter.strategy(d)
    assert last.dims == ("asset",)
    np.testing.assert_array_equal(last.values, adapter.calculate_weights(d).isel(time=-1).values)
