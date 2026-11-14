"""Incremental twin of research/predict/feats/book.py `BookStream`: one Binance bookTicker
stream (perp tick 0.1, spot tick 0.01), updated per message, read at the latest time q.

Decayed sums S = S * exp(-dt / tau) + x per event equal the offline `decay_sum`; a read at q
decays from the last event like `decayed_at`. The touch-depth normaliser is the 30 s
time-weighted EWMA (`ewma_level`). History of log mid / log microprice is kept for the
look-back features (dmic, dmid, basis and microprice deviations, the fair-value buckets)
and 330 s for the book staleness (perp microprice at the last Polymarket top change)."""
from __future__ import annotations

import math

from .series import Series

TAUS_OFI = (0.025, 0.1, 0.4, 1.6)
DMIC_W = (0.025, 0.05, 0.1, 0.25, 1.0)
DMID_W = (0.1, 1.0, 5.0)
# decayed sums: name -> tau (order fixes the offline feature order)
SUMS = (("ofi0.025", 0.025), ("ofi0.1", 0.1), ("ofi0.4", 0.4), ("ofi1.6", 1.6), ("depb", 0.1),
        ("depa", 0.1), ("lam", 0.1), ("up0.4", 0.4), ("dn0.4", 0.4), ("up2", 2.0), ("dn2", 2.0))
LMID, LMIC = 0, 1
NAN = float("nan")


class BookState:
    def __init__(self, tick: float, keep: float = 330.0):
        self.tick = tick
        self.t = None
        self.b = self.a = self.bq = self.aq = self.mid = NAN
        self.imb = self.spr = self.lq = NAN
        self.s = [0.0] * len(SUMS)
        self.num = self.den = 0.0
        self.depth = NAN
        self.hist = Series(2, keep)
        self.chg_t, self.chg_dir = None, 0.0
        self.mid_changed = False   # did the last update move the mid (decision forcing)

    def update(self, t: float, b: float, a: float, bq: float, aq: float) -> None:
        mid = (b + a) / 2
        q = bq + aq
        x_dep = q / 2
        if self.t is None:
            e = dep_b = dep_a = dm = 0.0
            self.num, self.den = x_dep, 1.0
            self.s = [0.0] * len(SUMS)
        else:
            dt = t - self.t
            pb, pa, pbq, paq = self.b, self.a, self.bq, self.aq
            e = (b >= pb) * bq - (b <= pb) * pbq - (a <= pa) * aq + (a >= pa) * paq
            dep_b = max(pbq - bq, 0.0) if b == pb else (pbq if b < pb else 0.0)
            dep_a = max(paq - aq, 0.0) if a == pa else (paq if a > pa else 0.0)
            dm = mid - self.mid
            d30 = math.exp(-dt / 30.0)
            self.num = self.num * d30 + x_dep
            self.den = self.den * d30 + 1.0
            dec = {tau: math.exp(-dt / tau) for tau in (0.025, 0.1, 0.4, 1.6, 2.0)}
            self.s = [v * dec[tau] for v, (_, tau) in zip(self.s, SUMS)]
        up, dn = float(dm > 0), float(dm < 0)
        for k, x in enumerate((e, e, e, e, dep_b, dep_a, 1.0, up, dn, up, dn)):
            self.s[k] += x
        self.depth = self.num / max(self.den, 1e-12)
        if dm != 0:
            self.chg_t, self.chg_dir = t, (1.0 if dm > 0 else -1.0)
        self.mid_changed = dm != 0
        lmid = math.log(mid)
        lmic = math.log((b * aq + a * bq) / q) if q > 0 else lmid
        self.imb = (bq - aq) / q if q > 0 else 0.0
        self.spr = min(max(float(round((a - b) / self.tick)), 0.0), 50.0)
        self.lq = math.log1p(q)
        self.t, self.b, self.a, self.bq, self.aq, self.mid = t, b, a, bq, aq, mid
        self.hist.add(t, lmid, lmic)

    def lmic(self, q: float) -> float:
        return self.hist.at(LMIC, q)

    def lmid(self, q: float) -> float:
        return self.hist.at(LMID, q)

    def decayed(self, k: int, q: float) -> float:
        return self.s[k] * math.exp(-(q - self.t) / SUMS[k][1]) if self.t is not None else 0.0

    def features(self, q: float, p: str, f: dict) -> None:
        """Fill f with the `p`-prefixed BookStream features at q (q >= the last update)."""
        have = self.t is not None
        f[f"{p}_imb"] = self.imb if have else 0.0
        f[f"{p}_spr"] = self.spr if have else 1.0
        f[f"{p}_lq"] = self.lq if have else 0.0
        dep = max(self.depth if have else 1.0, 1e-6)
        lmic, lmid = self.lmic(q), self.lmid(q)
        for w in DMIC_W:
            f[f"{p}_dmic{w:g}"] = 1e4 * (lmic - self.lmic(q - w))
        for w in DMID_W:
            f[f"{p}_dmid{w:g}"] = 1e4 * (lmid - self.lmid(q - w))
        f[f"{p}_micoff"] = 1e4 * (lmic - lmid)
        for k, (name, _) in enumerate(SUMS):
            v = self.decayed(k, q)
            if name.startswith("ofi") or name in ("depb", "depa"):
                f[f"{p}_{name}"] = v / dep
            elif name == "lam":
                f[f"{p}_lam"] = math.log1p(v / 0.1)
            else:
                f[f"{p}_{name}"] = v
        bq, aq = (self.bq, self.aq) if have else (1.0, 1.0)
        rb = self.decayed(4, q) / 0.1 + 1e-3 * dep
        ra = self.decayed(5, q) / 0.1 + 1e-3 * dep
        ttd_b, ttd_a = _log(bq / rb + 1e-4), _log(aq / ra + 1e-4)
        f[f"{p}_ttdb"], f[f"{p}_ttda"] = ttd_b, ttd_a
        f[f"{p}_ttd_rel"] = ttd_b - ttd_a
        f[f"{p}_ttd_min"] = min(ttd_b, ttd_a)
        if self.chg_t is not None:
            f[f"{p}_tsm"] = math.log(max(q - self.chg_t, 1e-3))
            f[f"{p}_lastdir"] = self.chg_dir
        else:
            f[f"{p}_tsm"], f[f"{p}_lastdir"] = 3.0, 0.0


def _log(x: float) -> float:
    return math.log(x) if x > 0 else (-math.inf if x == 0 else NAN)
