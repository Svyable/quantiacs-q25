import pandas as pd
import pytest
from research.prequential import quarterly_origins, validate_origins

def test_quarterly_origins_are_causal_complete_and_deterministic():
    args = ("2016-01-01", "2026-09-23")
    a = quarterly_origins(*args, min_train_days=730, forward_days=90, purge_days=30)
    b = quarterly_origins(*args, min_train_days=730, forward_days=90, purge_days=30)
    assert a == b
    validate_origins(a)
    assert len(a) >= 8
    assert all(x.train_end < x.forward_start <= x.forward_end for x in a)
    assert all((x.forward_end - x.forward_start).days == 89 for x in a)
    assert a[-1].forward_end <= pd.Timestamp(args[1])

def test_purge_is_exact_and_no_partial_recent_origin():
    origins = quarterly_origins("2016-01-01", "2026-09-23", purge_days=45)
    assert all((x.forward_start - x.train_end).days == 46 for x in origins)
    assert all(x.forward_start != pd.Timestamp("2026-07-01") for x in origins)

def test_origin_contract_fails_closed():
    with pytest.raises(ValueError):
        validate_origins(quarterly_origins("2024-01-01", "2025-01-01"))
    with pytest.raises(ValueError):
        quarterly_origins("2026-01-02", "2026-01-01")
