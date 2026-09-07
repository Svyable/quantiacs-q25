# baseline_sma_rsi — official Q24 guide SMA/RSI long-only liquid pattern
# Quantiacs Q25 Crypto Top-10 Long
#
# API_KEY is REQUIRED. Empty/blank does NOT work — the toolbox exits if API_KEY is ''.
# Create a free Quantiacs account and set your profile key:
#   export API_KEY=...   # from https://quantiacs.com/personalpage/homepage
#   or copy .env.example -> .env and fill API_KEY=

import os
import sys

# Prefer an already-exported API_KEY; do not pretend blank works.
if not os.environ.get("API_KEY"):
    # Allow dotenv-style local .env if present (optional, no dependency).
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    env_path = os.path.abspath(env_path)
    if os.path.isfile(env_path):
        with open(env_path, encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if not _line or _line.startswith("#") or "=" not in _line:
                    continue
                _k, _v = _line.split("=", 1)
                if _k.strip() == "API_KEY" and _v.strip() and "API_KEY" not in os.environ:
                    os.environ["API_KEY"] = _v.strip().strip('"').strip("'")
if not os.environ.get("API_KEY"):
    sys.exit(
        "API_KEY is missing or empty. Get a free profile key at "
        "https://quantiacs.com/personalpage/homepage and export API_KEY=..."
    )

import warnings

warnings.filterwarnings("ignore")

import xarray as xr
import numpy as np

import qnt.ta as qnta
import qnt.data as qndata
import qnt.output as qnout
import qnt.backtester as qnbt
import qnt.stats as qnstats

def load_data(period):
    return qndata.cryptodaily_load_data(tail=period)


def strategy(data):
    """SMA crossover + RSI band filter, liquid-only, long-only (Q24 guide)."""
    close = data.sel(field="close")
    is_liquid = data.sel(field="is_liquid")

    sma_fast = qnta.sma(close, 15)
    sma_slow = qnta.sma(close, 34)
    rsi = qnta.rsi(close, 14)

    sma_signal = xr.where(sma_fast > sma_slow, 1, 0)
    rsi_signal = xr.where((rsi < 34) | (rsi > 68), 1, 0)
    weights = sma_signal * rsi_signal * is_liquid
    # Multipass: return last-day weights when time dim present
    if "time" in getattr(weights, "dims", ()):
        weights = weights.isel(time=-1)
    return weights

if __name__ == "__main__":
    # Multipass with load_data (required for day-by-day slicing).
    # Official Q24 guide also shows single-pass over the full series.
    weights = qnbt.backtest(
        competition_type="crypto_daily_long",
        load_data=load_data,
        lookback_period=365,
        start_date="2016-01-01",
        strategy=strategy,
        analyze=True,
        check_correlation=True,
    )
