"""Top-of-book features of one Binance stream (perp or spot bookTicker) at query times.

Per update: mid, microprice (Stoikov's weighted mid), queue imbalance (Gould-Bonart), the
order-flow-imbalance increment e_i (Cont-Kukanov-Stoikov), queue depletion / replenishment
at the touch, and mid ticks. Decayed sums of these at several time scales are the event
intensities (Hawkes-style) of each kind; queue size over the depletion intensity is the
time-to-depletion of each side (Cont-de Larrard: the next price change is the first queue
to empty). Everything is read as of the query time on the receipt clock (no look-ahead)."""
from __future__ import annotations

import numpy as np

from .decay import at, decay_sum, decayed_at, ewma_level

TAUS_OFI = (0.025, 0.1, 0.4, 1.6)
DMIC_W = (0.025, 0.05, 0.1, 0.25, 1.0)
DMID_W = (0.1, 1.0, 5.0)


class BookStream:
    def __init__(self, bk: dict, tick: float):
        t = bk["t"]
        b, a = bk["b"], bk["a"]
        bq, aq = bk["bq"].astype(float), bk["aq"].astype(float)
        self.t, self.tick = t, tick
        mid = (b + a) / 2
        q = bq + aq
        self.lmid = np.log(mid)
        self.lmic = np.log(np.where(q > 0, (b * aq + a * bq) / np.where(q > 0, q, 1), mid))
        self.imb = np.where(q > 0, (bq - aq) / np.where(q > 0, q, 1), 0.0)
        self.spr = np.clip(np.rint((a - b) / tick), 0, 50)
        self.lq = np.log1p(q)
        pb, pa = np.r_[b[0], b[:-1]], np.r_[a[0], a[:-1]]
        pbq, paq = np.r_[bq[0], bq[:-1]], np.r_[aq[0], aq[:-1]]
        e = (b >= pb) * bq - (b <= pb) * pbq - (a <= pa) * aq + (a >= pa) * paq
        dep_b = np.where(b == pb, np.maximum(pbq - bq, 0), np.where(b < pb, pbq, 0.0))
        dep_a = np.where(a == pa, np.maximum(paq - aq, 0), np.where(a > pa, paq, 0.0))
        dm = np.r_[0.0, np.diff(mid)]
        self.depth = ewma_level(t, q / 2, 30.0)  # slow touch depth, normaliser
        self.s = {f"ofi{k}": decay_sum(t, e, k) for k in TAUS_OFI}
        self.s["depb"] = decay_sum(t, dep_b, 0.1)
        self.s["depa"] = decay_sum(t, dep_a, 0.1)
        self.s["lam"] = decay_sum(t, np.ones(len(t)), 0.1)
        self.s["up0.4"] = decay_sum(t, (dm > 0).astype(float), 0.4)
        self.s["dn0.4"] = decay_sum(t, (dm < 0).astype(float), 0.4)
        self.s["up2"] = decay_sum(t, (dm > 0).astype(float), 2.0)
        self.s["dn2"] = decay_sum(t, (dm < 0).astype(float), 2.0)
        self.bq, self.aq = bq, aq
        chg = np.flatnonzero(dm != 0)
        self.chg_t, self.chg_dir = t[chg], np.sign(dm[chg])

    def _tau(self, k: str) -> float:
        return {"depb": 0.1, "depa": 0.1, "lam": 0.1, "up0.4": 0.4, "dn0.4": 0.4,
                "up2": 2.0, "dn2": 2.0}.get(k) or float(k[3:])

    def level(self, name: str, q):
        return at(self.t, getattr(self, name), q)

    def features(self, q: np.ndarray, p: str) -> dict:
        f = {}
        f[f"{p}_imb"] = at(self.t, self.imb, q, 0.0)
        f[f"{p}_spr"] = at(self.t, self.spr, q, 1.0)
        f[f"{p}_lq"] = at(self.t, self.lq, q, 0.0)
        dep = at(self.t, self.depth, q, 1.0)
        dep = np.maximum(dep, 1e-6)
        lmic, lmid = at(self.t, self.lmic, q), at(self.t, self.lmid, q)
        for w in DMIC_W:
            f[f"{p}_dmic{w:g}"] = 1e4 * (lmic - at(self.t, self.lmic, q - w))
        for w in DMID_W:
            f[f"{p}_dmid{w:g}"] = 1e4 * (lmid - at(self.t, self.lmid, q - w))
        f[f"{p}_micoff"] = 1e4 * (lmic - lmid)
        for k, s in self.s.items():
            v = decayed_at(self.t, s, self._tau(k), q)
            if k.startswith("ofi"):
                f[f"{p}_{k}"] = v / dep
            elif k == "lam":
                f[f"{p}_lam"] = np.log1p(v / 0.1)
            elif k.startswith(("up", "dn")):
                f[f"{p}_{k}"] = v
            else:
                f[f"{p}_{k}"] = v / dep
        bq, aq = at(self.t, self.bq, q, 1.0), at(self.t, self.aq, q, 1.0)
        rb = decayed_at(self.t, self.s["depb"], 0.1, q) / 0.1 + 1e-3 * dep  # depletion BTC/s
        ra = decayed_at(self.t, self.s["depa"], 0.1, q) / 0.1 + 1e-3 * dep
        ttd_b, ttd_a = np.log(bq / rb + 1e-4), np.log(aq / ra + 1e-4)
        f[f"{p}_ttdb"], f[f"{p}_ttda"] = ttd_b, ttd_a
        f[f"{p}_ttd_rel"] = ttd_b - ttd_a          # > 0: ask empties first -> up tick
        f[f"{p}_ttd_min"] = np.minimum(ttd_b, ttd_a)
        i = np.searchsorted(self.chg_t, q, side="right") - 1
        ic = np.clip(i, 0, None)
        f[f"{p}_tsm"] = np.where(i >= 0, np.log(np.maximum(q - self.chg_t[ic], 1e-3)), 3.0)
        f[f"{p}_lastdir"] = np.where(i >= 0, self.chg_dir[ic], 0.0)
        return f
