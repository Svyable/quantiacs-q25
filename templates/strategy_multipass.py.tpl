# {{STRATEGY_NAME}}
# idea_id={{IDEA_ID}} desk={{DESK_ID}} family={{FAMILY}}
# thesis: {{THESIS}}
# params: {{PARAMS_COMMENT}}
#
# Quantiacs Q25 Crypto Top-10 Long — multipass template
# competition_type: crypto_daily_long | IS start: 2016-01-01 | long-only * is_liquid
#
# API_KEY is REQUIRED. Empty/blank does NOT work — the toolbox exits if API_KEY is ''.
# Free account + profile key: https://quantiacs.com/personalpage/homepage

import os
import sys

if not os.environ.get("API_KEY"):
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
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
{{STRATEGY_BODY}}


if __name__ == "__main__":
    # Multipass with load_data (day-by-day). Official Q24 guide also shows single-pass.
    weights = qnbt.backtest(
        competition_type="crypto_daily_long",
        load_data=load_data,
        lookback_period=365,
        start_date="2016-01-01",
        strategy=strategy,
        analyze=True,
        check_correlation=True,
    )
