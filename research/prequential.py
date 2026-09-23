"""Deterministic rolling-origin/prequential split construction for Research Mandate V2."""
from __future__ import annotations
from dataclasses import dataclass
import pandas as pd

@dataclass(frozen=True)
class Origin:
    train_end: pd.Timestamp
    forward_start: pd.Timestamp
    forward_end: pd.Timestamp

def quarterly_origins(start, end, *, min_train_days=730, forward_days=90, purge_days=0):
    """Build expanding-training quarterly forward origins without inspecting outcomes."""
    start, end = pd.Timestamp(start).normalize(), pd.Timestamp(end).normalize()
    if end < start or min_train_days < 1 or forward_days < 1 or purge_days < 0:
        raise ValueError("invalid rolling-origin parameters")
    earliest = start + pd.Timedelta(days=min_train_days + purge_days)
    out = []
    for forward_start in pd.date_range(earliest, end, freq="QS"):
        forward_end = forward_start + pd.Timedelta(days=forward_days - 1)
        if forward_end > end:
            continue
        train_end = forward_start - pd.Timedelta(days=purge_days + 1)
        out.append(Origin(train_end, forward_start, forward_end))
    return tuple(out)

def validate_origins(origins, *, minimum=8):
    """Fail closed on chronology or insufficient completed origins."""
    if len(origins) < minimum:
        raise ValueError(f"need at least {minimum} completed origins, got {len(origins)}")
    previous = None
    for origin in origins:
        if not origin.train_end < origin.forward_start <= origin.forward_end:
            raise ValueError("non-causal origin")
        if previous is not None and origin.forward_start <= previous:
            raise ValueError("origins are not strictly chronological")
        previous = origin.forward_start
