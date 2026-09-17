"""ONSET — fresh on-chain state learning for Quantiacs Q25 research.

No AEGIS/NOVA/MOSAIC signal or expert bank is used.
Sources: sponsor cryptodaily and six sponsor blockchain.com daily metrics.
MVRV/NVT are deliberately excluded: sponsor histories stop in October 2022.
Inputs are delayed 3 calendar days; missing observations cannot be carried
indefinitely. This is a conservative lag assumption, not proof of vintage data.

Research verdict (2026-09-16): not advanced. The fresh model failed the
recent-performance gate. Full historical Sharpe is not a competition forecast.

Install in Python 3.12 (tested runtime):
 pip install numpy==2.2.6 numba==0.61.2 llvmlite==0.44.0 pandas==2.2.3 xarray==2025.12.0 scipy==1.17.0
 pip install git+https://github.com/quantiacs/toolbox.git@9e5274c5ce102a66debc799fd2a2300969fb90f6
Notebook: import q25_onset; weights=q25_onset.submit()
Local cached research:
 python q25_onset.py --crypto crypto_data.nc --chain-dir fresh_alpha --end 2026-09-15

The notebook loads all data via Quantiacs; no saved model/files are required.
Blank API_KEY below falls back to public/default access. No external correlation
upload or contest entry is performed. Dataset eligibility and vintage timing
still require hosted confirmation before treating this as submission evidence.
"""

from __future__ import annotations
import os, json, argparse, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr

API_KEY = ""
if not os.environ.get("API_KEY", "").strip():
    os.environ["API_KEY"] = API_KEY or "default"
METRICS = (
    "n-transactions",
    "n-unique-addresses",
    "estimated-transaction-volume",
    "hash-rate",
    "difficulty",
    "miners-revenue",
)
LOOKBACK_DAYS = 1825
SELECTED_MODE = "chain"
MODES = ("chain", "combined", "price_control", "shuffled_control")


def panel(d, f):
    return d.sel(field=f).transpose("time", "asset").to_pandas().astype(float)


def cap_weights(score, budget=1.0, cap=0.25):
    out = np.zeros(len(score))
    active = np.isfinite(score) & (score > 0)
    while active.any() and budget > 1e-12:
        ids = np.flatnonzero(active)
        x = budget * score[active] / score[active].sum()
        hit = x > cap
        if not hit.any():
            out[ids] = x
            break
        out[ids[hit]] = cap
        budget -= cap * hit.sum()
        active[ids[hit]] = False
    return out


def basket(crypto):
    """Unforecasted, fully systematic diversified basket; only risk allocation."""
    c = panel(crypto, "close").where(lambda x: x > 0)
    r = c.pct_change(fill_method=None)
    sigma = r.rolling(28, min_periods=21).std().clip(lower=0.008)
    liquid = panel(crypto, "is_liquid").eq(1).to_numpy()
    known = panel(crypto, "is_liquid").ffill().eq(1).to_numpy()
    prices = c.to_numpy()
    rr = r.fillna(0).to_numpy()
    sv = sigma.to_numpy()
    n, a = c.shape
    weights = np.zeros((n, a))
    held = np.zeros(a)
    for t in range(n):
        held *= known[t]
        if t >= 63 and c.index[t].dayofweek in (0, 3):
            missing = ~np.isfinite(prices[t])
            locked = held * missing
            score = np.where(
                liquid[t] & np.isfinite(sv[t]) & ~missing,
                1 / np.nan_to_num(sv[t], nan=1),
                0,
            )
            target = cap_weights(score, 1 - locked.sum())
            ids = np.flatnonzero(target > 0)
            if len(ids):
                cov = np.atleast_2d(
                    np.cov(rr[max(0, t - 59) : t + 1, ids], rowvar=False)
                )
                cov = 0.5 * cov + 0.5 * np.diag(np.diag(cov))
                risk = np.sqrt(max(0, target[ids] @ cov @ target[ids]) * 365)
                target *= min(1.0, 0.30 / max(risk, 0.01))
            held = target + locked
        weights[t] = held
    w = xr.DataArray(
        weights, dims=["time", "asset"], coords={"time": c.index, "asset": c.columns}
    )
    return w, c, known


def feature_matrix(data, publication_lag=3):
    c = panel(data["crypto"], "close").where(lambda x: x > 0)
    index = c.index
    pieces = {}
    logs = {}
    for key in METRICS:
        series = data["chain"][key].sortby("time").to_pandas()
        if isinstance(series, pd.DataFrame):
            series = series.iloc[:, 0]
        series = series[~series.index.duplicated(keep="last")].sort_index()
        calendar = pd.date_range(
            series.index.min().normalize(), series.index.max().normalize(), freq="D"
        )
        series = series.reindex(calendar).ffill(limit=2).where(lambda x: x > 0)
        log = np.log(series)
        # Large one-day measurement spikes are tempered by a trailing median.
        smooth = log.rolling(7, min_periods=5).median()
        logs[key] = smooth
        feats = {
            "level": (smooth - smooth.rolling(252, min_periods=126).mean())
            / smooth.rolling(252, min_periods=126).std().clip(lower=0.02),
            "growth14": (smooth - smooth.shift(14)),
            "growth63": (smooth - smooth.shift(63)),
        }
        for name, x in feats.items():
            if name != "level":
                x = x / x.rolling(252, min_periods=126).std().clip(lower=0.02)
            # Calendar shift ensures observation dated t is first available t+lag.
            x = x.copy()
            x.index = x.index + pd.Timedelta(days=publication_lag)
            pieces[key + "_" + name] = x.reindex(index)
    for label, left, right in [
        ("revenue_per_hash", "miners-revenue", "hash-rate"),
        ("hash_per_difficulty", "hash-rate", "difficulty"),
        ("activity_per_address", "n-transactions", "n-unique-addresses"),
    ]:
        ratio = logs[left] - logs[right]
        x = (ratio - ratio.rolling(126, min_periods=84).mean()) / ratio.rolling(
            126, min_periods=84
        ).std().clip(lower=0.02)
        x.index = x.index + pd.Timedelta(days=publication_lag)
        pieces[label] = x.reindex(index)
    chain = (
        pd.DataFrame(pieces, index=index).replace([np.inf, -np.inf], np.nan).clip(-5, 5)
    )
    liq = panel(data["crypto"], "is_liquid").eq(1)
    market = (
        c.pct_change(fill_method=None)
        .where(liq.shift(1, fill_value=False))
        .mean(axis=1)
    )
    vol = market.rolling(28).std().clip(lower=0.003)
    price = pd.DataFrame(
        {
            f"price_{k}": market.rolling(k).sum() / (vol * np.sqrt(k))
            for k in (3, 7, 28, 84)
        },
        index=index,
    )
    price["volatility_ratio"] = vol / market.rolling(84).std().clip(lower=0.003)
    price = price.replace([np.inf, -np.inf], np.nan).clip(-5, 5)
    return chain, price


def forecasts(data, mode="chain", publication_lag=3):
    import qnt.stats as qs

    crypto = data["crypto"]
    base, c, known = basket(crypto)
    chain, price = feature_matrix(data, publication_lag)
    features = (
        price
        if mode == "price_control"
        else (pd.concat([chain, price], axis=1) if mode == "combined" else chain)
    )
    X = features.to_numpy()
    n = len(c)
    rr = (
        qs.calc_relative_return(crypto, base, slippage_factor=0.04, points_per_year=365)
        .to_pandas()
        .reindex(c.index)
        .fillna(0)
    )
    sigma = rr.rolling(28, min_periods=21).std().clip(lower=0.003).to_numpy()
    gross = base.sum("asset").to_numpy()
    labels = {}
    for h in (7, 21):
        # Forward labels are used only at rows where their entire outcome has
        # matured BEFORE each training decision; see rows ending at t-h-1 below.
        target = np.full(n, np.nan)
        vals = rr.to_numpy()
        for j in range(n - h):
            target[j] = (np.prod(1 + vals[j + 1 : j + h + 1]) - 1) / (
                sigma[j] * np.sqrt(h)
            )
        labels[h] = np.clip(target, -4, 4)
    predictions = np.zeros((n, 4))
    ready = np.zeros((n, 4), bool)
    anchors = np.flatnonzero(c.index.dayofweek == 0)
    days = c.index.values.astype("datetime64[D]").astype(np.int64)
    for p, t in enumerate(anchors):
        if t < 252:
            continue
        end = anchors[p + 1] if p + 1 < len(anchors) else n
        current = X[t:end]
        for col, (length, h) in enumerate([(365, 7), (1095, 7), (365, 21), (1095, 21)]):
            rows = np.arange(max(0, t - length), t - h)
            rows = rows[days[rows] % 3 == 0]
            eligible = np.isfinite(labels[h][rows]) & (gross[rows] > 0.05)
            rows = rows[eligible]
            if len(rows) < 75:
                continue
            train = X[rows]
            usable = np.mean(np.isfinite(train), axis=0) > 0.90
            if not usable.any():
                continue
            good = np.isfinite(train[:, usable]).all(axis=1)
            rows = rows[good]
            train = X[rows][:, usable]
            if len(rows) < 75:
                continue
            sw = np.exp2(-(t - rows) / (length / 2))
            sw /= sw.sum()
            mu = sw @ train
            sd = np.sqrt(sw @ ((train - mu) ** 2)).clip(0.1)
            xx = np.column_stack([np.ones(len(rows)), (train - mu) / sd])
            y = labels[h][rows].copy()
            if mode == "shuffled_control":
                y = np.roll(y, max(1, len(y) // 3))
            penalty = np.eye(xx.shape[1]) * 0.3
            penalty[0, 0] = 1e-6
            beta = np.linalg.solve(xx.T @ (xx * sw[:, None]) + penalty, xx.T @ (y * sw))
            ok = np.isfinite(current[:, usable]).all(axis=1)
            pred = (
                np.column_stack(
                    [np.ones(end - t), np.nan_to_num((current[:, usable] - mu) / sd)]
                )
                @ beta
            )
            predictions[t:end, col] = np.clip(pred, -2, 2)
            ready[t:end, col] = ok
    enough = ready.sum(axis=1) >= 3
    # Ensemble disagreement is a heuristic uncertainty penalty, not a CI.
    mean = predictions.mean(axis=1)
    disagreement = predictions.std(axis=1)
    exposure = np.where(enough, np.clip((mean - 0.25 * disagreement) / 0.25, 0, 1), 0)
    held = np.zeros(c.shape[1])
    weights = np.zeros_like(base.values)
    for t in range(n):
        held *= known[t]
        if c.index[t].dayofweek in (0, 3):
            target = base.values[t] * exposure[t]
            missing = ~np.isfinite(c.iloc[t].to_numpy())
            target[missing] = held[missing]
            target *= known[t]
            target /= max(1, target.sum())
            held = target
        weights[t] = held
    w = base.copy(data=weights)
    return w, {
        "base": base,
        "features": features,
        "predictions": predictions,
        "ready": ready,
        "exposure": exposure,
    }


def strategy(data, mode=SELECTED_MODE):
    return forecasts(data, mode)[0]


def strategy_last(data):
    return strategy(data).isel(time=-1)


def load_data(period=None, end=None, crypto_cache=None, chain_dir=None):
    import qnt.data as qd

    start = "2013-01-01"
    if period is not None:
        start = str(
            (
                pd.Timestamp(end or pd.Timestamp.now().date())
                - pd.Timedelta(days=period)
            ).date()
        )
    crypto = (
        xr.load_dataarray(crypto_cache)
        if crypto_cache
        else qd.cryptodaily.load_data(min_date=start, max_date=end)
    )
    crypto = crypto.sortby("time").sortby("asset").sel(time=slice(start, end))
    crypto.name = "cryptodaily"
    chain = {}
    for k in METRICS:
        x = (
            xr.load_dataarray(Path(chain_dir) / (k + ".nc"))
            if chain_dir
            else qd.blockchaincom.load_data(id=k, min_date=start, max_date=end)
        )
        chain[k] = x.sortby("time").sel(time=slice(start, end))
    return {"crypto": crypto, "chain": chain}


def window(data, max_date, lookback_period=LOOKBACK_DAYS):
    start = np.datetime64(max_date) - np.timedelta64(lookback_period, "D")
    return {
        "crypto": data["crypto"].sel(time=slice(start, max_date)),
        "chain": {
            k: v.sel(time=slice(start, max_date)) for k, v in data["chain"].items()
        },
    }


def submit():
    import qnt.output as qo

    d = load_data()
    w = qo.clean(strategy(d), d["crypto"], "crypto_daily_long")
    qo.check(
        w.sel(time=slice("2016", None)),
        d["crypto"],
        "crypto_daily_long",
        check_correlation=False,
    )
    qo.write(w)
    return w


def metrics(r):
    r = pd.Series(r).dropna()
    sd = r.std(ddof=0)
    eq = (1 + r).cumprod()
    return {
        "days": len(r),
        "sharpe": float(r.mean() / sd * np.sqrt(365)) if sd else 0.0,
        "cagr": float(eq.iloc[-1] ** (365 / len(r)) - 1),
        "max_drawdown": float((eq / eq.cummax().clip(lower=1) - 1).min()),
        "volatility": float(sd * np.sqrt(365)),
        "total_return": float(eq.iloc[-1] - 1),
    }


def backtest(data, out="onset_results", mode=SELECTED_MODE):
    import qnt.stats as qs, qnt.output as qo

    dest = Path(out)
    dest.mkdir(parents=True, exist_ok=True)
    d = data["crypto"]
    w, diag = forecasts(data, mode)
    clean = qo.clean(w, d, "crypto_daily_long", debug=False)
    delta = float(abs(clean - w).max())
    assert delta < 1e-9, delta
    rr = pd.DataFrame(
        {
            f"atr_{c:.2f}": qs.calc_relative_return(
                d,
                w.sel(time=slice("2016", None)),
                slippage_factor=c,
                points_per_year=365,
            ).to_pandas()
            for c in (0.04, 0.08, 0.12)
        }
    )
    rr.to_csv(dest / "returns.csv", index_label="time")
    w.to_pandas().to_csv(dest / "weights.csv", index_label="time")
    result = {
        "mode": mode,
        "last_date": str(rr.index[-1].date()),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "cleaner_delta": delta,
        "periods": {},
    }
    for k, start, end in [
        ("full", "2016", None),
        ("development", "2016", "2022"),
        ("later", "2023", None),
        ("recent", "2025", None),
        ("2026", "2026", None),
    ]:
        result["periods"][k] = {c: metrics(rr.loc[start:end, c]) for c in rr}
    (dest / "metrics.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--crypto")
    p.add_argument("--chain-dir")
    p.add_argument("--end")
    p.add_argument("--out", default="onset_results")
    p.add_argument("--mode", choices=MODES, default=SELECTED_MODE)
    a = p.parse_args()
    backtest(
        load_data(end=a.end, crypto_cache=a.crypto, chain_dir=a.chain_dir),
        a.out,
        a.mode,
    )
