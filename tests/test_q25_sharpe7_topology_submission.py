"""Parity test for the self-contained Sharpe7 + topology submission artifact."""
import numpy as np
import pandas as pd
import xarray as xr

from research import measure_sharpe7_topology_blend as measured
from submissions import q25_sharpe7_topology_equal_blend_multipass as packaged


def _panel(n=365, assets=7):
    rng=np.random.default_rng(20260919)
    common=rng.normal(0.0004,0.012,(n,1))
    idio=rng.normal(0.0,0.018,(n,assets))
    close=100.0*np.exp(np.cumsum(common+idio,axis=0))
    liquid=np.ones((n,assets),dtype=float)
    liquid[:35,-1]=0
    liquid[120:145,-2]=0
    liquid[250:258,0]=0
    return xr.DataArray(
        np.stack([close,liquid]),
        dims=("field","time","asset"),
        coords={
            "field":["close","is_liquid"],
            "time":pd.date_range("2025-01-01",periods=n,freq="D"),
            "asset":[f"A{i}" for i in range(assets)],
        },
        name="cryptodaily",
    )


def test_packaged_strategy_matches_measured_frozen_blend():
    data=_panel()
    expected=measured.strategy(data)
    actual=packaged.strategy(data)
    xr.testing.assert_allclose(actual.sel(asset=expected.asset),expected,rtol=0,atol=1e-12)
    assert float(actual.min()) >= -1e-12
    assert float(actual.max()) <= 0.25 + 1e-12
    assert float(actual.sum()) <= 1.0 + 1e-12


def test_packaged_artifact_has_no_project_strategy_imports():
    from pathlib import Path
    src=Path(packaged.__file__).read_text()
    assert "from strategies" not in src
    assert "from research" not in src
    assert "import strategies" not in src
    assert "import research" not in src
