"""Q25 preparation candidate: C165.
Sparse rank-mobility rotation with consensus risk budget.
Frozen historical model, not a promise of contest results.
No external datasets, local research imports, or account actions.
"""

from __future__ import annotations
from types import SimpleNamespace
import numpy as np
import pandas as pd
import xarray as xr

SOURCE_PROVENANCE = {'q25_roster_ready_v2/q25_c165_candidate.py': '9ddac6694546ab48441ab20926b72030772b84932a0a2260296ab6aa8c127de1'}

CANDIDATE_ID = 'C165'

NAME_CAP = 0.25

def _make_parent_engine():
    from dataclasses import dataclass
    from typing import Any
    import numpy as np
    import pandas as pd
    from scipy.special import ndtr
    EPS = 1e-12
    DATA_ORIGIN = '2014-01-01'
    CONTEST_START = '2016-01-01'
    COMPETITION_TYPE = 'crypto_daily_long'
    CANDIDATE = 'C165'
    FIELDS = ('open', 'high', 'low', 'close', 'vol', 'is_liquid')

    @dataclass(frozen=True)
    class MarketData:
        open: pd.DataFrame
        low: pd.DataFrame
        high: pd.DataFrame
        close_raw: pd.DataFrame
        volume_raw: pd.DataFrame
        liquid_raw: pd.DataFrame

    @dataclass(frozen=True)
    class Context:
        market: MarketData
        close: pd.DataFrame
        high: pd.DataFrame
        low: pd.DataFrame
        volume: pd.DataFrame
        liquid: pd.DataFrame
        observed: pd.DataFrame
        tradable: pd.DataFrame
        holdable: pd.DataFrame
        log_ret: pd.DataFrame
        atr_pct: pd.DataFrame

    @dataclass(frozen=True)
    class PortfolioSpec:
        names: int
        core_names: int
        exit_rank: int
        cap: float
        weekdays: tuple[int, ...]
        entry_score: float = 0.0
        hold_score: float = -0.15
        entry_trend: float = 0.35
        hold_trend: float = 0.15
        score_tilt: float = 0.65
        risk_floor: float = 0.02
        vol_target: float = 0.28

    def build_context(market: MarketData) -> Context:
        close_raw = market.close_raw
        observed = close_raw.notna() & (close_raw > 0.0)
        close = close_raw.where(observed).ffill()
        high_seed = market.high.where(market.high.notna() & (market.high > 0.0)).ffill()
        low_seed = market.low.where(market.low.notna() & (market.low > 0.0)).ffill()
        high = np.maximum(np.maximum(high_seed, low_seed), close)
        low = np.minimum(np.minimum(high_seed, low_seed), close)
        volume = market.volume_raw.where(market.volume_raw.notna() & (market.volume_raw >= 0.0), 0.0)
        liquid = (market.liquid_raw.fillna(0.0) > 0.0).astype(bool)
        valid_return = observed & observed.shift(1, fill_value=False)
        log_ret = np.log(close / (close.shift(1) + EPS)).where(valid_return)
        history = observed.rolling(126, min_periods=126).sum() >= 120
        recent_quotes = observed.rolling(7, min_periods=1).sum() >= 5
        active_volume = (volume > 0.0).rolling(30, min_periods=30).sum() >= 20
        tradable = (liquid & history & recent_quotes & active_volume & close.notna() & (close > 0.0)).astype(bool)
        holdable = (liquid & (observed.rolling(3, min_periods=1).sum() >= 1) & close.notna() & (close > 0.0)).astype(bool)
        prev_close = close.shift(1)
        true_range = np.maximum.reduce([(high - low).to_numpy(), (high - prev_close).abs().to_numpy(), (low - prev_close).abs().to_numpy()])
        true_range = pd.DataFrame(true_range, index=close.index, columns=close.columns)
        atr_pct = (true_range.rolling(14, min_periods=14).mean() / (close + EPS)).clip(0.0, 1.0)
        return Context(market=market, close=close, high=high, low=low, volume=volume, liquid=liquid, observed=observed, tradable=tradable, holdable=holdable, log_ret=log_ret, atr_pct=atr_pct)

    def centered_rank(values: pd.DataFrame, mask: pd.DataFrame) -> pd.DataFrame:
        frame = values.where(mask)
        ranks = frame.rank(axis=1, method='average')
        counts = frame.notna().sum(axis=1).astype(float)
        midpoint = (counts + 1.0) / 2.0
        denominator = (counts - 1.0).where(counts > 1.0)
        score = ranks.sub(midpoint, axis=0).mul(2.0).div(denominator, axis=0)
        score.loc[counts <= 1.0, :] = 0.0
        return score.where(frame.notna(), 0.0).fillna(0.0).clip(-1.0, 1.0)

    def smooth_score(score: pd.DataFrame, tradable: pd.DataFrame, window: int, lag: int, current_weight: float) -> pd.DataFrame:
        score = score.rolling(window, min_periods=max(2, window // 2)).mean().fillna(0.0)
        prior = score.shift(lag).where(score.shift(lag).notna(), score)
        stable = current_weight * score + (1.0 - current_weight) * prior
        return stable.where(tradable, 0.0).fillna(0.0).clip(-1.0, 1.0)

    def market_series(ctx: Context) -> tuple[pd.Series, pd.Series]:
        market_ret = ctx.log_ret.where(ctx.tradable).mean(axis=1, skipna=True).fillna(0.0)
        curve = np.exp(market_ret.cumsum())
        return (market_ret, curve)

    def rolling_beta(asset_ret: pd.DataFrame, market_ret: pd.Series, window: int=63, min_periods: int=42) -> pd.DataFrame:
        covariance = asset_ret.rolling(window, min_periods=min_periods).cov(market_ret)
        variance = market_ret.rolling(window, min_periods=min_periods).var(ddof=1)
        return covariance.div(variance + EPS, axis=0)

    def absolute_trend_gate(ctx: Context) -> pd.DataFrame:
        ma50 = ctx.close.rolling(50, min_periods=30).mean()
        ma150 = ctx.close.rolling(150, min_periods=90).mean()
        fast = ((np.log(ctx.close / (ma50 + EPS)) + 0.05) / 0.1).clip(0.0, 1.0)
        slow = ((np.log(ctx.close / (ma150 + EPS)) + 0.1) / 0.2).clip(0.0, 1.0)
        return (0.6 * fast + 0.4 * slow).fillna(0.0)

    def risk_multiplier(ctx: Context, floor: float, vol_target: float) -> pd.Series:
        market_ret, curve = market_series(ctx)
        fast_ma = curve.rolling(50, min_periods=30).mean()
        slow_ma = curve.rolling(150, min_periods=90).mean()
        fast = ((np.log(curve / (fast_ma + EPS)) + 0.08) / 0.16).clip(0.0, 1.0)
        slow = ((np.log(curve / (slow_ma + EPS)) + 0.12) / 0.24).clip(0.0, 1.0)
        asset_ma = ctx.close.rolling(100, min_periods=60).mean()
        breadth = (ctx.close > asset_ma).astype(float).where(ctx.tradable).mean(axis=1).fillna(0.5)
        breadth = ((breadth - 0.25) / 0.55).clip(0.0, 1.0)
        regime = (0.45 * fast + 0.35 * slow + 0.2 * breadth).rolling(7, min_periods=3).mean()
        gross = floor + (1.0 - floor) * regime.clip(0.0, 1.0)
        market_vol = market_ret.rolling(30, min_periods=20).std(ddof=1) * np.sqrt(365.25)
        vol_scale = (vol_target / (market_vol + EPS)).clip(0.2, 1.0).fillna(0.65)
        peak = curve.rolling(126, min_periods=63).max()
        drawdown = (1.0 - curve / (peak + EPS)).clip(0.0, 1.0)
        dd_scale = (1.0 - 0.88 * ((drawdown - 0.08) / 0.3).clip(0.0, 1.0)).clip(0.12, 1.0)
        return (gross * vol_scale * dd_scale).clip(floor, 1.0).fillna(0.2)

    def universe_change(liquid: pd.DataFrame) -> pd.Series:
        values = liquid.fillna(False).to_numpy(dtype=bool)
        changed = np.zeros(len(values), dtype=bool)
        if len(values) > 1:
            changed[1:] = np.any(values[1:] != values[:-1], axis=1)
        return pd.Series(changed, index=liquid.index)

    def buffered_top_n(score: pd.DataFrame, entry: pd.DataFrame, hold: pd.DataFrame, names: int, core_names: int, exit_rank: int, lag: int=7) -> pd.DataFrame:
        s = score.fillna(-np.inf).to_numpy(dtype=float)
        enter = entry.fillna(False).to_numpy(dtype=bool)
        keep = hold.fillna(False).to_numpy(dtype=bool)
        raw = np.zeros_like(enter)
        for i in range(len(s)):
            idx = np.flatnonzero(enter[i] & np.isfinite(s[i]))
            order = idx[np.argsort(-s[i, idx], kind='stable')]
            raw[i, order[:min(names, len(order))]] = True
        prior = np.zeros_like(raw)
        if len(raw) > lag:
            prior[lag:] = raw[:-lag]
        out = np.zeros_like(enter)
        for i in range(len(s)):
            entry_idx = np.flatnonzero(enter[i] & np.isfinite(s[i]))
            entry_order = entry_idx[np.argsort(-s[i, entry_idx], kind='stable')]
            hold_idx = np.flatnonzero(keep[i] & np.isfinite(s[i]))
            hold_order = hold_idx[np.argsort(-s[i, hold_idx], kind='stable')]
            chosen: list[int] = [int(x) for x in entry_order[:min(core_names, len(entry_order))]]
            for value in hold_order[:min(exit_rank, len(hold_order))]:
                value = int(value)
                if prior[i, value] and value not in chosen and (len(chosen) < names):
                    chosen.append(value)
            for value in entry_order:
                value = int(value)
                if value not in chosen and len(chosen) < names:
                    chosen.append(value)
            if chosen:
                out[i, chosen] = True
        return pd.DataFrame(out, index=score.index, columns=score.columns)

    def allocate_capped(raw: pd.DataFrame, cap: float) -> pd.DataFrame:
        values = raw.fillna(0.0).clip(lower=0.0).to_numpy(dtype=float)
        out = np.zeros_like(values)
        for i, source in enumerate(values):
            row = np.where(np.isfinite(source) & (source > 0.0), source, 0.0)
            active = row > 0.0
            remaining = 1.0
            for _ in range(values.shape[1] + 1):
                if not active.any() or remaining <= EPS:
                    break
                denominator = row[active].sum()
                if denominator <= EPS:
                    break
                active_idx = np.flatnonzero(active)
                proposal = remaining * row[active] / denominator
                capped = proposal > cap + EPS
                if not capped.any():
                    out[i, active_idx] = proposal
                    break
                capped_idx = active_idx[capped]
                out[i, capped_idx] = cap
                remaining -= cap * len(capped_idx)
                active[capped_idx] = False
        return pd.DataFrame(out, index=raw.index, columns=raw.columns)

    def weights_from_score(ctx: Context, score: pd.DataFrame, spec: PortfolioSpec, extra_entry: pd.DataFrame | None=None, extra_hold: pd.DataFrame | None=None, gross_override: pd.Series | None=None) -> pd.DataFrame:
        trend = absolute_trend_gate(ctx)
        entry = ctx.tradable & (score > spec.entry_score) & (trend > spec.entry_trend)
        hold = ctx.tradable & (score > spec.hold_score) & (trend > spec.hold_trend)
        if extra_entry is not None:
            entry &= extra_entry.fillna(False)
        if extra_hold is not None:
            hold &= extra_hold.fillna(False)
        selected = buffered_top_n(score, entry, hold, spec.names, spec.core_names, spec.exit_rank)
        realized_vol = ctx.log_ret.rolling(63, min_periods=42).std(ddof=1)
        risk = (0.7 * realized_vol + 0.3 * ctx.atr_pct).clip(0.003, 0.5)
        alpha_tilt = np.exp(spec.score_tilt * score.clip(-1.0, 1.0))
        trend_tilt = 0.3 + 0.7 * trend
        raw = (alpha_tilt * trend_tilt / (risk + EPS)).where(selected, 0.0)
        allocation = allocate_capped(raw, spec.cap)
        gross = gross_override.reindex(score.index).fillna(0.0) if gross_override is not None else risk_multiplier(ctx, spec.risk_floor, spec.vol_target)
        target = np.floor((allocation.mul(gross, axis=0) + EPS) / 0.01) * 0.01
        scheduled = pd.Series(score.index.dayofweek.isin(spec.weekdays) | universe_change(ctx.liquid).to_numpy(), index=score.index)
        weights = target.where(scheduled, np.nan, axis=0).ffill().fillna(0.0)
        weights = weights.where(ctx.holdable & ctx.liquid, 0.0).clip(lower=0.0)
        scale = (1.0 / (weights.sum(axis=1) + EPS)).where(weights.sum(axis=1) > 1.0, 1.0)
        return weights.mul(scale, axis=0).fillna(0.0)

    def _conditional_beta(asset_ret, market_ret, condition, window=126, min_periods=20):
        """Unchanged original conditional-beta estimator; not a new covariance fit."""
        market = market_ret.where(condition)
        asset = asset_ret.where(condition, axis=0)
        asset_mean = asset.rolling(window, min_periods=min_periods).mean()
        market_mean = market.rolling(window, min_periods=min_periods).mean()
        covariance = asset.sub(asset_mean).mul(market - market_mean, axis=0).rolling(window, min_periods=min_periods).mean()
        variance = ((market - market_mean) ** 2).rolling(window, min_periods=min_periods).mean()
        return covariance.div(variance + EPS, axis=0)

    def _cocrash126(ctx):
        market, _ = market_series(ctx)
        beta = rolling_beta(ctx.log_ret, market).clip(-1.0, 3.0)
        residual = ctx.log_ret - beta.mul(market, axis=0)
        hit = (residual > 0.0).where(residual.notna()).rolling(63, min_periods=42).mean()
        down_beta = _conditional_beta(ctx.log_ret, market, market < 0.0).clip(-1.0, 4.0)
        cocrash = (ctx.log_ret < -0.02).astype(float).where(market < -0.02, axis=0).rolling(126, min_periods=5).mean()
        down_vol = ctx.log_ret.clip(upper=0.0).rolling(63, min_periods=42).std(ddof=1)
        observed_columns = ctx.log_ret.notna().any(axis=0)
        skew = pd.DataFrame(np.nan, index=ctx.log_ret.index, columns=ctx.log_ret.columns)
        if observed_columns.any():
            skew.loc[:, observed_columns] = ctx.log_ret.loc[:, observed_columns].rolling(63, min_periods=42).skew()
        score = 0.32 * centered_rank(-cocrash, ctx.tradable) + 0.24 * centered_rank(-down_vol, ctx.tradable) + 0.2 * centered_rank(-down_beta, ctx.tradable) + 0.14 * centered_rank(hit, ctx.tradable) + 0.1 * centered_rank(skew, ctx.tradable)
        score = smooth_score(score.clip(-1.0, 1.0), ctx.tradable, 7, 14, 0.68)
        spec = PortfolioSpec(7, 5, 9, 0.2, (0,), entry_score=-0.1, hold_score=-0.3, entry_trend=0.0, hold_trend=0.0, score_tilt=0.66, risk_floor=0.03, vol_target=0.2)
        return weights_from_score(ctx, score, spec, (cocrash < 0.75) & (down_beta < 1.6), (cocrash < 0.9) & (down_beta < 2.0))

    def _trend_hit126(ctx):
        hit = (ctx.log_ret > 0.0).where(ctx.log_ret.notna()).rolling(126, min_periods=84).mean()
        score = centered_rank(hit, ctx.tradable).clip(-1.0, 1.0)
        score = smooth_score(score, ctx.tradable, 7, 14, 0.76)
        spec = PortfolioSpec(5, 3, 8, 0.25, (0,), entry_score=-0.1, hold_score=-0.3, entry_trend=0.0, hold_trend=0.0, score_tilt=0.74, risk_floor=0.03, vol_target=0.26)
        return weights_from_score(ctx, score, spec)

    def _historical_probability(state):
        history = state.shift(1)
        center = history.rolling(756, min_periods=378).mean()
        scale = history.rolling(756, min_periods=378).std(ddof=1).clip(lower=1e-06)
        z = ((state - center) / scale).clip(-8.0, 8.0)
        return pd.Series(ndtr(z.to_numpy(dtype=float)), index=state.index).fillna(0.5)

    def _c165(ctx):
        log_range = (np.log(ctx.high.where(ctx.high > 0.0)) - np.log(ctx.low.where(ctx.low > 0.0))).clip(0.0, 2.0).where(ctx.tradable)
        center = log_range.rolling(63, min_periods=32).median()
        scale = log_range.rolling(63, min_periods=32).std(ddof=1).clip(lower=0.0001)
        range_z = ((log_range - center) / scale).clip(-8.0, 8.0)
        ranked = range_z.where(ctx.tradable).rank(axis=1, pct=True, method='average')
        rank = (ranked - 0.5).where(range_z.notna() & ctx.tradable)
        move = rank.diff().abs()
        raw = (move.rolling(21, min_periods=10).mean() - move.rolling(84, min_periods=42).mean()).where(ctx.tradable)
        values = raw.where(ctx.tradable)
        score = values.sub(values.mean(axis=1), axis=0).div(values.std(axis=1, ddof=1).clip(lower=0.1), axis=0).clip(-6.0, 6.0)
        active = score.notna() & raw.notna() & ctx.tradable
        magnitude = raw.abs().where(active)
        threshold = magnitude.shift(1).rolling(252, min_periods=126).quantile(0.8)
        event_score = score.where(active & magnitude.ge(threshold) & score.gt(0.0))
        persisted = pd.DataFrame(np.nan, index=score.index, columns=score.columns)
        for age in range(7):
            candidate = event_score.shift(age) * (1.0 - 0.6 * age / 7)
            persisted = persisted.where(persisted.ge(candidate) | candidate.isna(), candidate)
        selection = persisted.where(ctx.tradable)
        ranks = selection.rank(axis=1, ascending=False, method='first')
        selected = selection.notna() & ranks.le(4)
        base = (selected.astype(float) / 4.0).where(ctx.holdable & ctx.liquid, 0.0).clip(0.0, 0.25).fillna(0.0)
        market = ctx.log_ret.where(ctx.tradable).mean(axis=1).fillna(0.0)
        curve = np.exp(market.cumsum().clip(-20.0, 20.0))
        probabilities = {}
        for horizon in (21, 63):
            state = np.log(curve / (curve.rolling(horizon, min_periods=max(14, horizon // 2)).mean() + EPS)).clip(-2.0, 2.0)
            probabilities[horizon] = _historical_probability(state).clip(0.0, 1.0)
        fused = np.exp(0.9 * np.log(probabilities[21].clip(lower=EPS)) + 0.1 * np.log(probabilities[63].clip(lower=EPS)))
        multiplier = fused.clip(0.0, 1.0).pow(2.0).clip(0.0, 1.0)
        return base.mul(multiplier.reindex(base.index).fillna(0.25), axis=0).fillna(0.0)

    def _validate_fields(fields, require_origin=True):
        missing = set(FIELDS) - set(fields)
        if missing:
            raise ValueError(f'Required fields missing: {sorted(missing)}')
        reference = fields['close']
        if not isinstance(reference, pd.DataFrame) or reference.empty:
            raise ValueError('Expected nonempty time-by-asset frames')
        index = reference.index
        if not isinstance(index, pd.DatetimeIndex) or index.tz is not None:
            raise ValueError('Expected timezone-naive DatetimeIndex')
        if not index.is_monotonic_increasing or not index.is_unique:
            raise ValueError('Dates must be sorted and unique')
        if not reference.columns.is_unique:
            raise ValueError('Asset coordinates must be unique')
        if require_origin and index[0] != pd.Timestamp(DATA_ORIGIN):
            raise ValueError('Full-prefix input from 2014-01-01 required; use load_data/window, not a rolling-tail loader')
        for name in FIELDS:
            frame = fields[name]
            if not frame.index.equals(index) or not frame.columns.equals(reference.columns):
                raise ValueError(f'Mismatched field coordinates: {name}')
            if np.isinf(frame.to_numpy(dtype=float)).any():
                raise ValueError(f'Infinite market input: {name}')

    def calculate_frames(fields, *, require_origin=True):
        """Pandas entry for parity tests; public adapters enforce the original origin."""
        _validate_fields(fields, require_origin=require_origin)
        market = MarketData(open=fields['open'], low=fields['low'], high=fields['high'], close_raw=fields['close'], volume_raw=fields['vol'], liquid_raw=fields['is_liquid'])
        ctx = build_context(market)
        functions = {'C165': _c165, 'CoCrash126': _cocrash126, 'Trend_hit126': _trend_hit126}
        if CANDIDATE not in functions:
            raise ValueError(f'Unknown frozen candidate: {CANDIDATE}')
        weights = functions[CANDIDATE](ctx)
        cap = 0.2 if CANDIDATE == 'CoCrash126' else 0.25
        values = weights.to_numpy(dtype=float)
        if not np.isfinite(values).all() or (values < -1e-12).any():
            raise ValueError('Invalid output weights')
        if (values > cap + 1e-12).any() or (weights.sum(axis=1) > 1.0 + 1e-12).any():
            raise ValueError('Frozen gross/name cap violated')
        if weights.where(~ctx.liquid, 0.0).abs().to_numpy().max() > 1e-12:
            raise ValueError('Non-liquid exposure')
        return weights

    def calculate_weights(data: Any):
        """Official xarray boundary. No execution shift and no cash normalization."""
        import xarray as xr
        if set(data.dims) != {'time', 'field', 'asset'}:
            raise ValueError('Expected field/time/asset dimensions')
        fields = {name: data.sel(field=name).transpose('time', 'asset').to_pandas().copy(deep=True) for name in FIELDS}
        weights = calculate_frames(fields)
        return xr.DataArray(weights.to_numpy(), dims=('time', 'asset'), coords={'time': weights.index, 'asset': weights.columns}, name='weights')
    return calculate_weights

_ENGINE = _make_parent_engine()

"""Common transparent I/O boundary; no alpha, sizing or execution optimization."""

DATA_ORIGIN = "2014-01-01"
CONTEST_START = "2016-01-01"
COMPETITION_TYPE = "crypto_daily_long"
EPS = 1e-12
REQUIRED_FIELDS = ("open", "high", "low", "close", "vol", "is_liquid")


def _validate_data(data):
    if set(data.dims) != {"field", "time", "asset"}:
        raise ValueError("expected field/time/asset dimensions")
    times = pd.DatetimeIndex(data.time.values)
    if len(times) == 0 or times[0] != pd.Timestamp(DATA_ORIGIN):
        raise ValueError("a full causal prefix beginning 2014-01-01 is required")
    if not times.is_monotonic_increasing or times.has_duplicates or times.hasnans:
        raise ValueError("timestamps must be valid, unique and ascending")
    if pd.Index(data.asset.values).has_duplicates:
        raise ValueError("asset coordinates must be unique")
    if not set(REQUIRED_FIELDS).issubset(set(data.field.values.tolist())):
        raise ValueError("required sponsor OHLCV/liquidity field missing")


def _allowed_positions(data):
    close = data.sel(field="close").transpose("time", "asset")
    liquid = data.sel(field="is_liquid").transpose("time", "asset")
    return np.isfinite(close) & (close > 0.0) & (liquid.fillna(0.0) > 0.0)


def _validate_weights(data, weights):
    if set(weights.dims) != {"time", "asset"}:
        raise ValueError("weights must have time/asset dimensions")
    # Compare dimension indexes, not unrelated scalar coordinates such as field='close'.
    if not weights.time.to_index().equals(data.time.to_index()) or not weights.asset.to_index().equals(data.asset.to_index()):
        raise ValueError("weights must preserve input coordinates")
    values = weights.transpose("time", "asset").values
    if not np.isfinite(values).all() or values.min(initial=0.0) < -EPS:
        raise ValueError("weights must be finite and long-only")
    if values.max(initial=0.0) > NAME_CAP + EPS or values.sum(axis=1).max(initial=0.0) > 1.0 + EPS:
        raise ValueError("name or gross cap violated")
    forbidden = weights.where(~_allowed_positions(data), 0.0).fillna(0.0)
    if np.abs(forbidden.values).max(initial=0.0) > EPS:
        raise ValueError("exposure without an observed liquid price")


def calculate_weights(data):
    """Frozen parent targets; preserve cash and add no extra execution lag."""
    _validate_data(data)
    raw = _ENGINE(data).transpose("time", "asset")
    if not np.isfinite(raw.values).all():
        raise ValueError("the parent produced non-finite weights")
    weights = raw.where(_allowed_positions(data), 0.0)
    _validate_weights(data, weights)
    return weights


def strategy(data):
    """End-of-prefix target; the sponsor supplies the execution lag."""
    return calculate_weights(data).isel(time=-1, drop=True)


def load_data(period=None):
    """Do not truncate online state: load the complete fixed origin."""
    import qnt.data as qndata
    return qndata.cryptodaily_load_data(min_date=DATA_ORIGIN)


def window(data, max_date, lookback_period):
    return data.sel(time=slice(DATA_ORIGIN, max_date))


def clean_and_validate(data, weights):
    import qnt.output as qnout
    cleaned = qnout.clean(weights.copy(deep=True), data, COMPETITION_TYPE, debug=False)
    cleaned = cleaned.sel(time=weights.time, asset=weights.asset)
    # Some toolbox versions forward-fill positions at NaN quotes/liquidity.
    # Reapply safety, never normalize intentionally uninvested cash away.
    cleaned = cleaned.where(_allowed_positions(data), 0.0).fillna(0.0)
    _validate_weights(data, cleaned)
    drift = float(np.max(np.abs(cleaned.values - weights.values), initial=0.0))
    if drift > EPS:
        raise RuntimeError(f"cleaner changed a valid target by {drift}; stop for review")
    return cleaned


def run(*, write_output=False, check_correlation=False):
    """Read-only diagnostics by default. Neither branch submits an entry."""
    import qnt.output as qnout
    import qnt.stats as qnstats
    data = load_data()
    weights = clean_and_validate(data, calculate_weights(data))
    qnout.check(weights, data, COMPETITION_TYPE, check_correlation=check_correlation)
    stats = qnstats.calc_stat(data, weights.sel(time=slice(CONTEST_START, None)))
    print(CANDIDATE_ID)
    print(stats.isel(time=-1).to_pandas())
    if write_output:
        qnout.write(weights)
    else:
        print("Diagnostic only: no weights written and no submission made.")
    return weights


def run_multipass(*, allow_output_artifacts=False, check_correlation=False):
    """Hosted replay can write local output artifacts; require explicit opt-in."""
    if not allow_output_artifacts:
        raise RuntimeError("Set allow_output_artifacts=True only for the intended hosted replay.")
    import qnt.backtester as qnbt
    return qnbt.backtest(
        competition_type=COMPETITION_TYPE, load_data=load_data, window=window,
        lookback_period=5000, start_date=CONTEST_START, strategy=strategy,
        analyze=True, build_plots=False, check_correlation=check_correlation,
    )


if __name__ == "__main__":
    run(write_output=False, check_correlation=False)
