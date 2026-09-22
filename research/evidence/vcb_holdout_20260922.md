# VCB one-shot holdout evidence — 2026-09-22

Experiment: `vcb_holdout_20260922`

This is the immutable result of the preregistered one-shot holdout protocol. No holdout retuning is permitted after observing these results.

Source: GitHub Actions workflow `q25-vcb-holdout`, run `35789392059`, artifact `10720919001` (`vcb-holdout-evidence`), artifact digest `sha256:72967cbeb3cb0de39ba88ce87d1bbfb589c21d2df3d8650c01f72ded4ba59297`.

Evaluation uses official 4% ATR transaction cost. Holdout is 2023-01-01 through 2026-09-21.

## Frozen VCB candidate

- Full 2016→latest Sharpe: `1.6351605012677333`
- Full annualized return: `0.5516855274326908`
- Full annualized volatility: `0.33738922081653233`
- Full max drawdown: `-0.21717925449771047`
- Full 10%-vol normalized return: `0.1635160501267733`
- Holdout Sharpe: `0.8585320387763733`
- Holdout annualized return: `0.15792035232474455`
- Holdout annualized volatility: `0.18394229358035527`
- Holdout max drawdown: `-0.20039586847614532`
- Holdout 10%-vol normalized return: `0.0858532038776373`

## Qualified incumbent

- Holdout Sharpe: `0.700104542224771`
- Holdout annualized return: `0.3170448553886787`
- Holdout annualized volatility: `0.4528535900955349`
- Holdout max drawdown: `-0.48932033421755494`
- Holdout 10%-vol normalized return: `0.07001045422247715`

Candidate/incumbent holdout daily-return correlation: `0.38560580388688276`.

## Preselected 50/50 blend

- Holdout Sharpe: `0.8626436022810139`
- Holdout annualized return: `0.23748260385671166`
- Holdout annualized volatility: `0.27529631382967074`
- Holdout max drawdown: `-0.28550993503686706`
- Holdout 10%-vol normalized return: `0.08626436022810138`

## Frozen gates

- Candidate full 2016→latest Sharpe > 1: PASS
- Candidate holdout Sharpe > 0: PASS
- Candidate holdout 10%-vol normalized return > 0: PASS
- No holdout retuning: PASS

Decision emitted by the frozen evaluator: `ADVANCE`.

Interpretation: VCB survived the untouched holdout and materially improves risk-adjusted holdout economics versus the incumbent. The preselected 50/50 blend is marginally stronger on holdout Sharpe and 10%-vol normalized return than standalone VCB, while VCB has materially lower holdout drawdown than the incumbent. These observations do not authorize post-hoc parameter changes.