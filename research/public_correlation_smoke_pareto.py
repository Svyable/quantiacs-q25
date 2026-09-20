"""Public/default Quantiacs correlation smoke for frozen Pareto skyline."""
from __future__ import annotations

import os

os.environ.setdefault("API_KEY", "default")

import qnt.backtester as qnbt
import qnt.data as qndata
import qnt.output as qnout
import qnt.stats as qnstats

from submissions import q25_pareto_skyline_multipass as s

START = "2016-01-01"


def main():
    result = qnbt.backtest(
        competition_type=s.COMPETITION_TYPE,
        load_data=s.load_data,
        lookback_period=s.LOOKBACK_DAYS,
        start_date=START,
        strategy=s.strategy,
        analyze=False,
        build_plots=False,
        check_correlation=False,
    )
    weights = result[0] if isinstance(result, tuple) else result
    data = qndata.cryptodaily_load_data(min_date="2015-01-01")
    clean = qnout.clean(weights, data, s.COMPETITION_TYPE).sel(
        time=slice(START, None)
    )
    print("candidate: pareto_skyline")
    print("submission_blob: 04a3afd9b47525fd9a773455466a71494a393fc9")
    print("participant_id:", os.environ.get("PARTICIPANT_ID", "0"))
    qnstats.check_correlation(clean, data, print_stack_trace=True)


if __name__ == "__main__":
    main()
