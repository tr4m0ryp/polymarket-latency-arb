"""Per-market decision table: features at every decision instant plus forward targets.

Decision instants (receipt clock, inside [start + 3, end - 5]): every perp and spot
bookTicker update and every change of our view of the Up book's top, thinned to at most one
per 20 ms unless the perp or spot mid changed or the perp microprice moved >= 0.002 bp since
the last kept row (the leaders' trigger size), so no trigger-sized event is dropped.

Targets (never read by a decision): Binance perp / spot mid and perp microprice moves at
t + h (bp), the venue Up mid / ask / bid at t + h, and for each L the venue Up ask / bid at
the match time t + L + 150 ms and the venue mid 1 / 3 / 10 s after it."""
from __future__ import annotations

import numpy as np

from ...strategy.signals.fair import Fair
from ...strategy.signals.feeds import Feeds
from ...strategy import OUT as SOUT
from .. import H_MS, HOLD, L_MS, TICK_PERP
from .book import BookStream
from .flow import TradeStream
from .pm import fair_columns, pm_features

_FAIR = {}


def _fair(name: str) -> Fair:
    if name not in _FAIR:
        _FAIR[name] = Fair.load(SOUT / f"fair-{name}.json")
    return _FAIR[name]


def decision_times(perp: BookStream, spot: BookStream, book, start: float, end: float,
                   gap: float = 0.02, thr_bp: float = 0.002) -> np.ndarray:
    top = np.flatnonzero((np.diff(book.bb_r) != 0) | (np.diff(book.ba_r) != 0)) + 1
    tt = book.t0 + top * 0.005
    t = np.concatenate([perp.t, spot.t, tt])
    force = np.concatenate([np.r_[False, np.diff(perp.lmid) != 0], np.r_[False, np.diff(spot.lmid) != 0],
                            np.ones(len(tt), bool)])
    o = np.argsort(t, kind="stable")
    t, force = t[o], force[o]
    w = (t > start + 3) & (t < end - 5)
    t, force = t[w], force[w]
    mic = perp.level("lmic", t) * 1e4
    keep = np.zeros(len(t), bool)
    last_t, last_m = -np.inf, np.nan
    for i in range(len(t)):
        if force[i] or t[i] - last_t >= gap or abs(mic[i] - last_m) >= thr_bp:
            keep[i] = True
            last_t, last_m = t[i], mic[i]
    return np.unique(t[keep])


def table(m: dict, book, ftr: dict | None) -> dict | None:
    meta = m["meta"]
    if not m["perp"] or len(m["perp"].get("t", [])) < 1000:
        return None
    fd = Feeds(m)
    if np.isnan(fd.K):
        return None
    perp = BookStream(m["perp"], TICK_PERP)
    spot = BookStream(m["spot_bk"], 0.01)
    q = decision_times(perp, spot, book, meta["start"], meta["end"])
    f = {"t": q}
    f.update(perp.features(q, "p"))
    f.update(spot.features(q, "s"))
    sdep = np.maximum(np.interp(q, spot.t, spot.depth), 1e-6)
    pdep = np.maximum(np.interp(q, perp.t, perp.depth), 1e-6)
    st = m["spot_tr"]
    f.update(TradeStream({"t": st["t"], "q": st["q"], "m": st["m"]}, 0.5).features(q, "st", sdep))
    if ftr is not None and len(ftr["t"]) > 100:
        f.update(TradeStream(ftr, 1.0).features(q, "ft", pdep))
    basis = 1e4 * (perp.level("lmid", q) - spot.level("lmid", q))
    bslow = 1e4 * (perp.level("lmid", q - 30) - spot.level("lmid", q - 30))
    f["basis_dev"] = basis - bslow
    f["mic_dev"] = 1e4 * ((perp.level("lmic", q) - perp.level("lmic", q - 2))
                          - (spot.level("lmic", q) - spot.level("lmic", q - 2)))
    f.update(pm_features(q, book, fd, perp))
    fc = fair_columns(q, fd)
    import pandas as pd
    dfc = pd.DataFrame(fc)
    f["fair_dz"] = _fair("pzm").dz(dfc)
    f["fair_p"] = _fair("pzm").p(dfc.assign(mid=f["pm_mid"]))
    # targets
    lm0, sm0, lc0 = perp.level("lmid", q), spot.level("lmid", q), perp.level("lmic", q)
    for h in H_MS:
        qh = q + h / 1000
        f[f"y_pm{h}"] = 1e4 * (perp.level("lmid", qh) - lm0)
        f[f"y_sm{h}"] = 1e4 * (spot.level("lmid", qh) - sm0)
        f[f"y_pc{h}"] = 1e4 * (perp.level("lmic", qh) - lc0)
        gh = book.g_ceil(qh)
        f[f"y_dm{h}"] = 100 * (book.mid(gh) - f["pm_mid"])
        f[f"y_au{h}"] = book.ba[gh] - f["pm_ba"]
        f[f"y_bu{h}"] = book.bb[gh] - f["pm_bb"]
    for L in L_MS:
        tm = q + L / 1000 + HOLD
        g = book.g_ceil(tm)
        f[f"x_ba{L}"], f[f"x_bb{L}"] = book.ba[g].astype(float), book.bb[g].astype(float)
        f[f"x_bad{L}"] = book.bad[g].astype(float)
        for k in (1, 3, 10):
            mk = book.mid(book.g_ceil(tm + k))
            if m["outcome"] is not None:  # past the close the token is worth its outcome
                mk = np.where(tm + k > meta["end"], float(m["outcome"]), mk)
            f[f"x_m{k}_{L}"] = mk
    f["outcome"] = np.full(len(q), np.nan if m["outcome"] is None else float(m["outcome"]))
    return {k: (v if k == "t" else np.asarray(v, dtype=np.float32)) for k, v in f.items()}
