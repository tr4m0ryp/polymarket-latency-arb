"""Per-fill latency features for one BTC up/down family.

Every fill gets, in addition to the YES-frame columns of study.wallets.frame:
  mo{L}       markout after L s: q * (next print >= ts+L  -  pi), in USD.
              Positive = the book moved toward the side the fill took.
  r{k}        BTC log move over the k seconds before the fill second,
              log(S[ts-1] / S[ts-1-k]) on Binance 1 s closes (only data a
              trader could have seen when the fill printed).
  rf10        BTC log move over the 10 s after the fill (ex-post check).
  fair        Up probability implied by spot S[ts-1] under the family's
              real settlement rule (fair_up); 0.5 before any of the strike is
              observable (TWAP families: from start-60 s on).
  fair_stale  the same with spot 10 s older: fair - fair_stale is what the
              newest 10 s of spot did to the fair price."""
from __future__ import annotations

import sys
from math import erf
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from study.wallets import load_fills, load_markets  # noqa: E402
from study.wallets.score import copy_prices  # noqa: E402

from spot import Spot  # noqa: E402

MO_LAGS = (2, 10, 60)
LOOKBACKS = (1, 3, 10, 30)
_erf = np.vectorize(erf, otypes=[float])


def phi(z: np.ndarray) -> np.ndarray:
    return 0.5 * (1 + _erf(np.clip(z, -30, 30) / np.sqrt(2)))


def family_frame(slug: str, with_spot: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    mk = load_markets(slug)
    f = load_fills(slug, mk)
    f["series"] = slug
    f["start_ts"] = f["condition_id"].map(mk["start_ts"]).astype(np.int64)
    f["usd"] = f["size"] * f["price"]
    for lag in MO_LAGS:
        cp = copy_prices(f, lag)
        f[f"mo{lag}"] = np.where(np.isnan(cp), 0.0, f["q"] * (cp - f["pi"]))
    if with_spot:
        add_spot(f, mk)
    return f, mk


# 5m and 15m resolve on Chainlink's 60 s TWAP (end TWAP >= start TWAP);
# hourly and longer on the Binance candle (close >= open). Checked against
# Gamma descriptions and reproduced from Binance 1 s data (99.0 % / 99.0 % / 100 % agreement).
TWAP_FAMILIES = {"btc-up-or-down-5m", "btc-up-or-down-15m"}
TW = 60


def fair_up(sp: Spot, slug: str, ts, start, end, s_now) -> np.ndarray:
    """P(Up) given spot s_now at second ts, driftless Brownian spot with the
    trailing 300 s per-second vol. 0.5 while the strike is still unseen."""
    tau = np.clip(end - ts, 1, None).astype(float)
    sig = sp.vol(ts - 1) * s_now
    if slug in TWAP_FAMILIES:
        # strike = TWAP over [start-60, start): partly known inside that span
        pre = ts < start
        done = np.clip(ts - (start - TW), 0, TW).astype(float)
        k_seen = sp.mean(start - TW, np.maximum(ts, start - TW + 1))
        k = np.where(pre, (done * k_seen + (TW - done) * s_now) / TW, sp.mean(start - TW, start))
        late = tau < TW
        seen = sp.mean(end - TW, ts)
        mu = np.where(late, ((TW - tau) * seen + tau * s_now) / TW, s_now)
        var = np.where(late, tau ** 3 / 3 / TW ** 2, tau - 2 * TW / 3)
        live = ts >= start - TW
    else:
        k = sp.at(start - 1)
        mu, var = s_now, tau
        live = ts >= start
    p = phi((mu - k) / (sig * np.sqrt(var)))
    return np.where(live, p, 0.5)


def add_spot(f: pd.DataFrame, mk: pd.DataFrame) -> None:
    slug = f["series"].iloc[0]
    sp = Spot(int(mk["start_ts"].min()) - 3600, int(mk["end_ts"].max()) + 120)
    ts = f["ts"].to_numpy(np.int64)
    now = sp.at(ts - 1)
    for k in LOOKBACKS:
        f[f"r{k}"] = np.log(now / sp.at(ts - 1 - k))
    f["rf10"] = np.log(sp.at(ts + 9) / now)
    st = f["start_ts"].to_numpy(np.int64)
    en = f["end_ts"].to_numpy(np.int64)
    f["fair"] = fair_up(sp, slug, ts, st, en, now)
    f["fair_stale"] = fair_up(sp, slug, ts, st, en, sp.at(ts - 11))
    # sanity: share of resolved outcomes the Binance proxy reproduces
    o, e = mk["start_ts"].to_numpy(np.int64), mk["end_ts"].to_numpy(np.int64)
    if slug in TWAP_FAMILIES:
        up = sp.mean(e - TW, e) >= sp.mean(o - TW, o)
    else:
        up = sp.at(e - 1) >= sp.at(o - 1)
    f.attrs["spot_outcome_agree"] = float((up == (mk["R"].to_numpy() == 1)).mean())
