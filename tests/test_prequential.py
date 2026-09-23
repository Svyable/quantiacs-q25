import pandas as pd
import pytest

from research.prequential import (
    exponential_recency_weights,
    rolling_origins,
    weighted_mean,
)


def test_rolling_origins_are_strictly_causal_and_do_not_cross_live_start():
    idx = pd.date_range("2016-01-01", "2026-09-23", freq="D")
    windows = rolling_origins(idx, min_train_days=365, forward_days=90, step_days=90)
    assert len(windows) >= 8
    assert all(w.train_end == w.origin for w in windows)
    assert all(w.score_start > w.origin for w in windows)
    assert all(w.score_end >= w.score_start for w in windows)
    assert all(w.score_end < pd.Timestamp("2026-10-01") for w in windows)
    assert all(w.origin + pd.Timedelta(days=90) <= idx[-1] for w in windows)
    assert [w.origin for w in windows] == sorted({w.origin for w in windows})


def test_min_train_days_is_inclusive_calendar_span():
    idx = pd.date_range("2020-01-01", "2020-04-30", freq="D")
    windows = rolling_origins(
        idx,
        min_train_days=10,
        forward_days=10,
        step_days=10,
        live_start="2021-01-01",
    )
    assert windows
    first = windows[0]
    assert first.origin == pd.Timestamp("2020-01-10")
    assert (first.train_end - first.train_start).days + 1 == 10


def test_rolling_origins_exclude_incomplete_latest_forward_window():
    idx = pd.date_range("2020-01-01", "2021-12-15", freq="D")
    windows = rolling_origins(idx, min_train_days=365, forward_days=90, step_days=90, live_start="2022-01-01")
    assert windows
    assert all(w.origin + pd.Timedelta(days=90) <= idx[-1] for w in windows)
    assert windows[-1].origin <= idx[-1] - pd.Timedelta(days=90)


def test_rolling_origin_prefix_is_invariant_to_appending_future_history():
    early = pd.date_range("2016-01-01", "2024-12-31", freq="D")
    later = pd.date_range("2016-01-01", "2026-09-23", freq="D")
    a = rolling_origins(early, min_train_days=365, forward_days=90, step_days=90)
    b = rolling_origins(later, min_train_days=365, forward_days=90, step_days=90)
    by_origin = {w.origin: w for w in b}
    comparable = [w for w in a if w.score_end <= early[-1] - pd.Timedelta(days=1)]
    assert comparable
    for w in comparable:
        assert by_origin[w.origin] == w


def test_rolling_origins_advance_across_sparse_calendar_gaps():
    # Several scheduled 30-day targets fall inside this 120-day data outage.
    # The scheduler must advance its calendar target rather than repeatedly
    # selecting the same last observation (the historical implementation could
    # loop forever here).
    idx = pd.DatetimeIndex(
        list(pd.date_range("2020-01-01", "2020-03-31", freq="D"))
        + list(pd.date_range("2020-08-01", "2021-03-31", freq="D"))
    )
    windows = rolling_origins(
        idx,
        min_train_days=30,
        forward_days=20,
        step_days=30,
        live_start="2022-01-01",
    )
    origins = [w.origin for w in windows]
    assert origins
    assert origins == sorted(set(origins))
    assert any(origin >= pd.Timestamp("2020-08-01") for origin in origins)


def test_recency_weights_are_normalized_monotone_and_half_life_consistent():
    idx = pd.DatetimeIndex(["2022-01-01", "2024-01-01", "2026-01-01"])
    w = exponential_recency_weights(idx, half_life_days=730, as_of="2026-01-01")
    assert w.sum() == pytest.approx(1.0)
    assert w.iloc[0] < w.iloc[1] < w.iloc[2]
    assert (w.iloc[1] / w.iloc[2]) == pytest.approx(0.5, rel=0.01)


def test_recency_refuses_future_observations():
    with pytest.raises(ValueError, match="future observations"):
        exponential_recency_weights(["2026-01-01", "2026-02-01"], as_of="2026-01-15")


def test_weighted_mean_aligns_without_imputation():
    x = pd.Series([1.0, 3.0], index=pd.to_datetime(["2026-01-01", "2026-01-02"]))
    w = pd.Series([0.25, 0.75], index=x.index)
    assert weighted_mean(x, w) == pytest.approx(2.5)
