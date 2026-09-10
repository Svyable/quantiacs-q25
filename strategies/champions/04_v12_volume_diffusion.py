"""Q25 preparation candidate: V12.
Signed cross-asset volume diffusion.
Frozen historical model, not a promise of contest results.
No external datasets, local research imports, or account actions.
"""

from __future__ import annotations
from types import SimpleNamespace
import numpy as np
import pandas as pd
import xarray as xr

SOURCE_PROVENANCE = {'entry_review_restore/q25_v12_signed_volume_diffusion_bundle/q25_v12_signed_volume_diffusion_submission.py': '6333ed5800d8933185d4045d627bf92ac3b10ca5ccc459e8cd3cc5219f2ed304'}

CANDIDATE_ID = 'V12'

NAME_CAP = 0.25

def _make_parent_engine():
    import warnings
    from dataclasses import dataclass
    from typing import Any
    import numpy as np
    import pandas as pd
    import xarray as xr
    EPS = 1e-12
    ANN = 365.0
    MIN_DATE = '2013-01-01'
    CONTEST_START = '2016-01-01'
    COMPETITION_TYPE = 'crypto_daily_long'
    LOOKBACK_DAYS = 5000
    PM_REPORT_ENABLED = True

    @dataclass(frozen=True)
    class Context:
        index: pd.DatetimeIndex
        columns: pd.Index
        close: pd.DataFrame
        volume: pd.DataFrame
        liquid: pd.DataFrame
        tradable: pd.DataFrame
        holdable: pd.DataFrame
        log_ret: pd.DataFrame

    def _field(data: xr.DataArray, name: str) -> pd.DataFrame:
        selected = data.sel(field=name).transpose('time', 'asset')
        return pd.DataFrame(np.asarray(selected.values, dtype=float), index=pd.DatetimeIndex(selected.time.values, name='time'), columns=pd.Index(selected.asset.values, name='asset'))

    def _safe_log_ratio(left: pd.DataFrame, right: pd.DataFrame) -> pd.DataFrame:
        valid = left.notna() & right.notna() & (left > 0.0) & (right > 0.0)
        return np.log(left.where(valid, 1.0) / right.where(valid, 1.0)).where(valid)

    def _context(data: xr.DataArray) -> Context:
        if not {'time', 'field', 'asset'}.issubset(data.dims):
            raise ValueError(f'expected time/field/asset dimensions, got {data.dims}')
        index = pd.DatetimeIndex(data.time.values, name='time')
        columns = pd.Index(data.asset.values, name='asset')
        if not index.is_monotonic_increasing or index.has_duplicates or columns.has_duplicates:
            raise ValueError('time and asset coordinates must be ordered and unique')
        close_raw = _field(data, 'close')
        volume_raw = _field(data, 'vol')
        liquid = (_field(data, 'is_liquid').fillna(0.0) > 0.0).astype(bool)
        observed = close_raw.notna() & (close_raw > 0.0)
        close = close_raw.where(observed).ffill()
        volume = volume_raw.where(volume_raw.notna() & (volume_raw >= 0.0), 0.0)
        valid_return = observed & observed.shift(1, fill_value=False)
        log_ret = _safe_log_ratio(close, close.shift(1)).where(valid_return)
        history = observed.rolling(126, min_periods=126).sum() >= 120
        recent_quotes = observed.rolling(7, min_periods=1).sum() >= 5
        active_volume = (volume > 0.0).rolling(30, min_periods=30).sum() >= 20
        tradable = (liquid & history & recent_quotes & active_volume & close.notna() & (close > 0.0)).astype(bool)
        holdable = (liquid & (observed.rolling(3, min_periods=1).sum() >= 1) & close.notna() & (close > 0.0)).astype(bool)
        return Context(index, columns, close, volume, liquid, tradable, holdable, log_ret)

    def _rolling_beta(asset: pd.DataFrame, market: pd.Series) -> pd.DataFrame:
        covariance = asset.rolling(126, min_periods=63).cov(market)
        variance = market.rolling(126, min_periods=63).var(ddof=1)
        return covariance.div(variance + EPS, axis=0)

    def _residual_z(ctx: Context) -> pd.DataFrame:
        market = ctx.log_ret.where(ctx.tradable).mean(axis=1, skipna=True).fillna(0.0)
        beta = _rolling_beta(ctx.log_ret, market).clip(-1.0, 3.0)
        residual = (ctx.log_ret - beta.mul(market, axis=0)).where(ctx.tradable)
        scale = residual.rolling(63, min_periods=32).std(ddof=1).clip(0.002, 0.5)
        return (residual / (scale + EPS)).clip(-6.0, 6.0)

    def _volume_z(ctx: Context) -> pd.DataFrame:
        dollar = (ctx.close * ctx.volume).where((ctx.close > 0.0) & (ctx.volume > 0.0))
        log_volume = np.log(dollar.where(dollar > 0.0, 1.0)).where(dollar > 0.0)
        center = log_volume.rolling(63, min_periods=32).median()
        scale = log_volume.rolling(63, min_periods=32).std(ddof=1)
        return ((log_volume - center) / (scale + EPS)).clip(-6.0, 6.0)

    def _lagged_correlation(x: np.ndarray, y: np.ndarray, x_mask: np.ndarray, y_mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        x0 = np.where(x_mask, x, 0.0)
        y0 = np.where(y_mask, y, 0.0)
        mx = x_mask.astype(float)
        my = y_mask.astype(float)
        count = mx.T @ my
        safe_count = np.maximum(count, 1.0)
        mean_x = x0.T @ my / safe_count
        mean_y = mx.T @ y0 / safe_count
        covariance = x0.T @ y0 / safe_count - mean_x * mean_y
        var_x = (x0 * x0).T @ my / safe_count - mean_x * mean_x
        var_y = mx.T @ (y0 * y0) / safe_count - mean_y * mean_y
        denominator = np.sqrt(np.maximum(var_x, 0.0) * np.maximum(var_y, 0.0))
        correlation = np.divide(covariance, denominator, out=np.zeros_like(covariance), where=(denominator > EPS) & (count >= 126))
        correlation = np.nan_to_num(correlation, nan=0.0, posinf=0.0, neginf=0.0)
        np.fill_diagonal(correlation, 0.0)
        return (np.clip(correlation, -0.75, 0.75), count)

    def _signed_links(correlation: np.ndarray, count: np.ndarray) -> np.ndarray:
        t_value = np.abs(correlation) * np.sqrt(np.maximum(count - 2.0, 0.0)) / np.sqrt(np.maximum(1.0 - correlation * correlation, 1e-06))
        relation = np.where(t_value >= 2.0, correlation, 0.0)
        k = min(6, relation.shape[0])
        order = np.argpartition(np.abs(relation), -k, axis=0)[-k:, :]
        sparse = np.zeros_like(relation)
        columns = np.broadcast_to(np.arange(relation.shape[1]), order.shape)
        sparse[order, columns] = relation[order, columns]
        return sparse

    def _diffusion_score(ctx: Context) -> pd.DataFrame:
        rz = _residual_z(ctx)
        vz = _volume_z(ctx)
        mondays = np.flatnonzero(ctx.index.weekday == 0)
        mondays = mondays[mondays >= 260]
        raw = np.full((len(mondays), len(ctx.columns)), np.nan)
        for place, row in enumerate(mondays):
            start = row - 252
            x = vz.iloc[start:row].to_numpy(dtype=float)
            y = rz.iloc[start + 1:row + 1].to_numpy(dtype=float)
            correlation, count = _lagged_correlation(x, y, np.isfinite(x), np.isfinite(y))
            prediction = vz.iloc[row].fillna(0.0).to_numpy(dtype=float) @ _signed_links(correlation, count)
            valid = ctx.tradable.iloc[row].to_numpy(dtype=bool)
            raw[place, valid] = prediction[valid]
        weekly = pd.DataFrame(raw, index=ctx.index[mondays], columns=ctx.columns)
        expanded = weekly.reindex(ctx.index).ffill().fillna(0.0).where(ctx.tradable)
        center = expanded.mean(axis=1)
        scale = expanded.std(axis=1, ddof=1).clip(lower=0.1)
        return expanded.sub(center, axis=0).div(scale, axis=0).clip(-6.0, 6.0)

    def _allocate_capped(raw: pd.DataFrame, cap: float) -> pd.DataFrame:
        values = raw.fillna(0.0).clip(lower=0.0).to_numpy(dtype=float)
        output = np.zeros_like(values)
        for row_location, source in enumerate(values):
            row = np.where(np.isfinite(source) & (source > 0.0), source, 0.0)
            active = row > 0.0
            remaining = 1.0
            for _ in range(values.shape[1] + 1):
                if not active.any() or remaining <= EPS:
                    break
                denominator = row[active].sum()
                if denominator <= EPS:
                    break
                locations = np.flatnonzero(active)
                proposal = remaining * row[active] / denominator
                capped = proposal > cap + EPS
                if not capped.any():
                    output[row_location, locations] = proposal
                    break
                capped_locations = locations[capped]
                output[row_location, capped_locations] = cap
                remaining -= cap * len(capped_locations)
                active[capped_locations] = False
        return pd.DataFrame(output, index=raw.index, columns=raw.columns)

    def _construction(ctx: Context, score: pd.DataFrame, names: int, cap: float, minimum: float) -> pd.DataFrame:
        active = (score > 0.0) & ctx.tradable
        opportunity = score.where(active).max(axis=1)
        threshold = opportunity.shift(1).rolling(252, min_periods=126).quantile(0.75)
        day_gate = opportunity.ge(threshold).fillna(False)
        gate = pd.DataFrame(np.broadcast_to(day_gate.to_numpy(dtype=bool)[:, None], score.shape), index=ctx.index, columns=ctx.columns)
        eligible = active & gate & score.ge(minimum)
        rank = score.where(eligible).rank(axis=1, ascending=False, method='first')
        raw = np.exp(0.28 * score.clip(-3.0, 3.0)).where(eligible & rank.le(names), 0.0)
        target = _allocate_capped(raw, cap).ewm(alpha=0.33, adjust=False).mean()
        target = target.where(ctx.holdable & ctx.liquid, 0.0).clip(lower=0.0)
        target = np.floor((target + EPS) / 0.005) * 0.005
        gross = target.sum(axis=1)
        return target.mul(np.minimum(1.0, 1.0 / (gross + EPS)), axis=0).fillna(0.0)

    def calculate_weights(data: xr.DataArray) -> xr.DataArray:
        ctx = _context(data)
        score = _diffusion_score(ctx)
        six = _construction(ctx, score, 6, 0.2, 0.0)
        five = _construction(ctx, score, 5, 0.25, 0.1)
        blend = (0.5 * six + 0.5 * five).where(ctx.holdable & ctx.liquid, 0.0).clip(lower=0.0)
        gross = blend.sum(axis=1)
        blend = blend.mul(np.minimum(1.0, 1.0 / (gross + EPS)), axis=0).fillna(0.0)
        return xr.DataArray(blend.to_numpy(dtype=float), coords={'time': ctx.index, 'asset': ctx.columns}, dims=('time', 'asset'), name='weights')
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
