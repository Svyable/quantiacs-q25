import numpy as np
import pandas as pd
import pytest
from research.mechanism_diagnostics import paired_block_interval, allocation_difference
from test_frontier_c import panel


def test_paired_identical_streams_have_exactly_zero_difference():
    x = pd.Series(np.sin(np.arange(200)) * .01, index=pd.date_range('2020-01-01', periods=200))
    result = paired_block_interval(x, x)
    assert result['annualized_mean_difference'] == 0.
    assert result['percentile_95_interval'] == [0., 0.]
    assert result['selection_adjusted'] is False


def test_pairing_preserves_constant_advantage_and_rejects_gaps():
    x = pd.Series(np.sin(np.arange(200)) * .01, index=pd.date_range('2020-01-01', periods=200))
    r = paired_block_interval(x + .001, x)
    np.testing.assert_allclose(r['percentile_95_interval'], [.365, .365])
    with pytest.raises(ValueError, match='contiguous'):
        paired_block_interval(x.drop(x.index[50]), x.drop(x.index[50]))
    with pytest.raises(ValueError, match='match exactly'):
        paired_block_interval(x, x.iloc[1:])


def test_allocator_identity_requires_aligned_assets():
    x = panel().sel(field='close', drop=True).transpose('time','asset') * 0
    assert allocation_difference(x, x)['status'] == 'IDENTICAL_TARGETS'
    assert allocation_difference(x, x + .1)['status'] == 'DISTINCT_TARGETS'
    with pytest.raises(ValueError, match='coordinates'):
        allocation_difference(x, x.sel(asset=x.asset.values[::-1]))
