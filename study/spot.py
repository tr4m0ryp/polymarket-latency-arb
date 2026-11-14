"""Binance BTCUSDT 1-second closes, cached per UTC hour.

Cache layout: data/cache/prices/binance_btcusdt_1s/<hour_ts>.npy holds a
float64 array of 3600 closes for seconds [hour_ts, hour_ts + 3600). A second
without trades carries the previous close (Binance already emits zero-volume
candles with the carried price). Missing seconds are NaN.
Writes go through a temp file + rename, so concurrent runs cannot corrupt it."""
from __future__ import annotations

import json
import os
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "cache" / "prices" / "binance_btcusdt_1s"
HOSTS = ("https://api.binance.com", "https://data-api.binance.vision")


def _get(url: str) -> list:
    last = None
    for attempt in range(6):
        for host in HOSTS:
            try:
                req = urllib.request.Request(host + url, headers={"User-Agent": "btclat/0.1"})
                with urllib.request.urlopen(req, timeout=20) as r:
                    return json.loads(r.read())
            except Exception as e:  # network or 429: back off, then try the mirror
                last = e
        time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"binance fetch failed: {url}: {last}")


def _fetch_hour(h: int) -> np.ndarray:
    out = np.full(3600, np.nan)
    for k in range(4):  # 4 pages of 900 s each (limit 1000)
        s = h + 900 * k
        rows = _get(f"/api/v3/klines?symbol=BTCUSDT&interval=1s"
                    f"&startTime={s * 1000}&endTime={(s + 899) * 1000 + 999}&limit=1000")
        for r in rows:
            i = r[0] // 1000 - h
            if 0 <= i < 3600:
                out[i] = float(r[4])
    return out


def hour(h: int) -> np.ndarray:
    p = CACHE / f"{h}.npy"
    if p.exists():
        return np.load(p)
    arr = _fetch_hour(h)
    if h + 3600 < time.time() - 120:  # only cache complete hours
        CACHE.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(f".tmp{os.getpid()}.npy")
        np.save(tmp, arr)
        os.replace(tmp, p)
    return arr


class Spot:
    """Dense per-second close series over [t0, t1)."""

    def __init__(self, t0: int, t1: int, workers: int = 8):
        h0, h1 = t0 - t0 % 3600, t1 - t1 % 3600 + 3600
        hours = list(range(h0, h1, 3600))
        with ThreadPoolExecutor(workers) as ex:
            parts = list(ex.map(hour, hours))
        self.t0 = h0
        px = np.concatenate(parts)
        # forward-fill isolated gaps
        idx = np.where(np.isnan(px), 0, np.arange(len(px)))
        np.maximum.accumulate(idx, out=idx)
        self.px = px[idx]

    def at(self, ts) -> np.ndarray:
        """Close of the second [ts, ts+1); NaN outside the range."""
        i = np.asarray(ts, dtype=np.int64) - self.t0
        ok = (i >= 0) & (i < len(self.px))
        out = np.full(i.shape, np.nan)
        out[ok] = self.px[i[ok]]
        return out

    def logret(self, ts, a: int, b: int) -> np.ndarray:
        """log(S[ts+b] / S[ts+a]) using second closes."""
        return np.log(self.at(np.asarray(ts) + b) / self.at(np.asarray(ts) + a))

    def vol(self, ts, window: int = 300) -> np.ndarray:
        """Trailing per-second log-return stdev over `window` seconds."""
        lr = np.diff(np.log(self.px), prepend=np.log(self.px[0]))
        c1 = np.concatenate([[0], np.cumsum(lr)])
        c2 = np.concatenate([[0], np.cumsum(lr ** 2)])
        i = np.clip(np.asarray(ts, dtype=np.int64) - self.t0, window, len(self.px))
        n = window
        m = (c1[i] - c1[i - n]) / n
        v = (c2[i] - c2[i - n]) / n - m ** 2
        return np.sqrt(np.clip(v, 1e-12, None))

    def mean(self, a, b) -> np.ndarray:
        """Mean close over seconds [a, b) (vectorised; a < b)."""
        if not hasattr(self, "_c"):
            self._c = np.concatenate([[0.0], np.cumsum(self.px)])
        n = len(self.px)
        ia = np.clip(np.asarray(a, dtype=np.int64) - self.t0, 0, n)
        ib = np.clip(np.asarray(b, dtype=np.int64) - self.t0, 0, n)
        return (self._c[ib] - self._c[ia]) / np.maximum(ib - ia, 1)
