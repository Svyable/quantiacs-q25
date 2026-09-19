"""Public/default Quantiacs correlation smoke test for exact production artifacts.

This uses PARTICIPANT_ID=0 unless the environment provides a real participant
identifier. Therefore: a warning is actionable; "Ok" is not account clearance.
"""
from __future__ import annotations

import importlib
import os

os.environ.setdefault("API_KEY", "default")

import qnt.backtester as qnbt
import qnt.data as qndata
import qnt.output as qnout
import qnt.stats as qnstats

CANDIDATE = os.environ["CANDIDATE"]
START = "2016-01-01"


def _load_candidate():
    if CANDIDATE == "sharpe7":
        module = importlib.import_module("submissions.q25_sharpe7_vol2_multipass")
        strategy = lambda d: module.strategy(d, {"window": 7}, "base")
    elif CANDIDATE == "sota":
        module = importlib.import_module("submissions.q25_sota_meta_ensemble_multipass")
        strategy = module.strategy
    elif CANDIDATE == "sharpe7_topology":
        module = importlib.import_module(
            "submissions.q25_sharpe7_topology_blend_multipass"
        )
        strategy = module.strategy
    else:
        raise ValueError(CANDIDATE)
    return module, strategy


def main():
    module, strategy = _load_candidate()
    result = qnbt.backtest(
        competition_type=module.COMPETITION_TYPE,
        load_data=module.load_data,
        lookback_period=module.LOOKBACK_DAYS,
        start_date=START,
        strategy=strategy,
        analyze=False,
        build_plots=False,
        check_correlation=False,
    )
    if isinstance(result, tuple):
        result = result[0]
    data = qndata.cryptodaily_load_data(min_date="2015-01-01")
    clean = qnout.clean(result, data, "crypto_daily_long").sel(
        time=slice(START, None)
    )
    print("candidate:", CANDIDATE)
    print("participant_id:", os.environ.get("PARTICIPANT_ID", "0"))
    qnstats.check_correlation(clean, data, print_stack_trace=True)


if __name__ == "__main__":
    main()
