"""Platform cleaner translation must be attributable, never a broad waiver."""
import numpy as np
import pandas as pd
import xarray as xr

from research.benchmark import cleaner_impact


def panel():
    times = pd.date_range("2020-01-01", periods=3)
    assets = ["A", "B", "C"]
    close = np.full((3, 3), 100.0)
    liquid = np.ones((3, 3))
    close[1, 0] = np.nan
    liquid[2, 2] = 0.0  # ordinary explicit illiquidity is not a cleaner-translation waiver
    fields = ["close", "is_liquid"]
    return xr.DataArray(
        np.stack([close, liquid]), dims=("field", "time", "asset"),
        coords={"field": fields, "time": times, "asset": assets}, name="cryptodaily",
    )


def weights(values):
    d = panel()
    return xr.DataArray(np.asarray(values, float), dims=("time", "asset"),
                        coords={"time": d.time, "asset": d.asset})


def test_direct_ambiguous_cell_can_explain_same_day_cross_sectional_normalization():
    raw = weights([[.2, .2, .2], [0, .2, .2], [.2, .2, 0]])
    cleaned = weights([[.2, .2, .2], [.2, .16, .16], [.2, .2, 0]])
    impact = cleaner_impact(raw, cleaned, panel())
    assert impact["status"] == "PLATFORM_DATA_TRANSLATION"
    assert impact["translation_days"] == 1
    assert impact["direct_ambiguous_data_changes"] == 1
    assert impact["same_day_normalization_changes"] == 2
    assert impact["unexplained_changed_cells"] == 0


def test_unrelated_day_mutation_remains_unexplained_even_with_illiquid_assets_elsewhere():
    raw = weights([[.2, .2, .2], [0, .2, .2], [.2, .2, 0]])
    cleaned = raw.copy(deep=True)
    cleaned.loc[dict(time=cleaned.time.values[0], asset="B")] = .1
    impact = cleaner_impact(raw, cleaned, panel())
    assert impact["status"] == "UNEXPLAINED_MUTATION"
    assert impact["translation_days"] == 0
    assert impact["unexplained_changed_cells"] == 1


def test_explicit_is_liquid_zero_does_not_create_an_ambiguity_waiver():
    raw = weights([[.2, .2, .2], [0, .2, .2], [.2, .2, 0]])
    cleaned = raw.copy(deep=True)
    cleaned.loc[dict(time=cleaned.time.values[2], asset="C")] = .1
    impact = cleaner_impact(raw, cleaned, panel())
    assert impact["status"] == "UNEXPLAINED_MUTATION"
    assert impact["direct_ambiguous_data_changes"] == 0
    assert impact["unexplained_changed_cells"] == 1
