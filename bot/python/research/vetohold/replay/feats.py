"""Decision-time features on what the bot had received (receipt clock, no look-ahead).

Book: the research grid replayed on receipt times (`rsz`, 5 ms rows). Level age = time
since the seen level's size last changed (or the last snapshot). Binance: perp and spot
book mids, moves over trailing windows in bp, signed toward the order's side."""
from __future__ import annotations

import numpy as np

WIN = (0.1, 0.25, 0.5, 1.0, 3.0)


class Ctx:
    """Per-market arrays the features read."""

    def __init__(self, m: dict, rsz: np.ndarray, t0: float, dt: float):
        ev = m["ev"]
        self.rsz, self.t0, self.dt = rsz, t0, dt
        side, tick = ev["side"].astype(int), ev["tick"].astype(int)
        col = np.where(side > 0, tick, 100 + tick)
        self.snap_t = np.sort(ev["t"][side == 0])
        o = np.lexsort((ev["t"], col))
        c, t = col[o], ev["t"][o]
        self.col_t = {int(k): t[c == k] for k in np.unique(c[side[o] != 0])}
        o = np.argsort(ev["t"], kind="stable")
        self.ev_t, self.ev_lag = ev["t"][o], (ev["t"] - ev["ts"])[o]   # receipt - venue stamp
        tr = m["tr"]
        self.tr_t, self.tr_sz = (tr["t"], tr["size"]) if len(tr) else (np.zeros(0), np.zeros(0))
        if len(tr):   # venue-clock prints mapped to the Up-book column they consumed
            k = np.rint(tr["px"].astype(float) * 100).astype(int)
            up, buy = tr["up"] == 1, tr["side"] > 0
            col = np.where(up, np.where(buy, 100 + k, k), np.where(buy, 100 - k, 200 - k))
            o = np.argsort(tr["ts"], kind="stable")
            self.pr_ts, self.pr_col, self.pr_sz = tr["ts"][o], col[o], tr["size"][o].astype(float)
        else:
            self.pr_ts = self.pr_col = self.pr_sz = np.zeros(0)
        self.perp = self._mid(m.get("perp") or {}, "b", "a")
        self.spot = self._mid(m.get("spot_bk") or {}, "b", "a")

    @staticmethod
    def _mid(d: dict, b: str, a: str):
        if not d or not len(d.get("t", [])):
            return np.zeros(0), np.zeros(0)
        return d["t"], (d[b] + d[a]) / 2

    def trades_on(self, cols: np.ndarray, a: float, b: float) -> float:
        """Shares printed on these Up-book columns with venue time in (a, b]."""
        i, j = np.searchsorted(self.pr_ts, a, "right"), np.searchsorted(self.pr_ts, b, "right")
        return float(self.pr_sz[i:j][np.isin(self.pr_col[i:j], cols)].sum())

    def g(self, t: float) -> int:
        return int(np.clip(np.floor((t - self.t0) / self.dt + 1e-9), 0, len(self.rsz) - 1))

    def mid_at(self, ser, t: float) -> float:
        ts, v = ser
        i = np.searchsorted(ts, t, side="right") - 1
        return float(v[i]) if i >= 0 else np.nan


def features(c: Ctx, o, cols: np.ndarray, s_idx: int) -> dict:
    t, side = o.t, int(o.side)
    row = c.rsz[c.g(t)]
    a = row[cols]
    dep = lambda r, k: float(r[cols[:s_idx + k + 1]].sum())  # noqa: E731
    best = np.flatnonzero(a > 0)
    opp = row[np.arange(1, 100)] if side > 0 else row[200 - np.arange(1, 100)]  # our-frame bids by tick
    nb = np.flatnonzero(opp > 0)
    f = {"f_seen": o.seen, "f_dep0": float(a[s_idx]) if s_idx < len(a) else 0.0,
         "f_dep2": dep(row, 2), "f_dep5": dep(row, 5),
         "f_spread": (o.seen - (nb[-1] + 1) / 100) if len(nb) else np.nan,
         "f_bid_dep": float(opp[nb[-1]]) if len(nb) else 0.0,
         "f_best_gap": (s_idx - best[0]) if len(best) else np.nan}
    lt = c.col_t.get(int(cols[s_idx]), np.zeros(0)) if s_idx < len(cols) else np.zeros(0)
    i = np.searchsorted(lt, t, side="right") - 1
    j = np.searchsorted(c.snap_t, t, side="right") - 1
    last = max(lt[i] if i >= 0 else -np.inf, c.snap_t[j] if j >= 0 else -np.inf)
    f["f_age"] = min(t - last, 60.0)
    for w in (0.25, 1.0):
        r0 = c.rsz[c.g(t - w)]
        f[f"f_ddep_{w}"] = dep(row, 2) - dep(r0, 2)
        b0 = np.flatnonzero(r0[cols] > 0)
        f[f"f_dask_{w}"] = ((best[0] - b0[0]) if len(best) and len(b0) else 0) / 100
        f[f"f_nev_{w}"] = float(np.searchsorted(c.ev_t, t, "right") - np.searchsorted(c.ev_t, t - w))
    k0, k1 = np.searchsorted(c.tr_t, t - 1.0), np.searchsorted(c.tr_t, t, "right")
    f["f_trd_1"] = float(c.tr_sz[k0:k1].sum())
    e = np.searchsorted(c.ev_t, t, "right")   # feed lag the bot can see: venue stamps it received
    lag = c.ev_lag[max(0, e - 50):e]
    f["f_rlag"] = float(lag[-1]) if len(lag) else np.nan
    f["f_rlag50"] = float(np.nanmedian(lag)) if len(lag) else np.nan
    for name, ser in (("perp", c.perp), ("spot", c.spot)):
        now = c.mid_at(ser, t)
        for w in WIN:
            f[f"f_{name}_{w}"] = side * (now / c.mid_at(ser, t - w) - 1) * 1e4
    f["f_fresh"] = abs(f["f_perp_0.25"]) / (abs(f["f_perp_3.0"]) + 0.5)
    ts, v = c.perp
    i0, i1 = np.searchsorted(ts, t - 30.0), np.searchsorted(ts, t, "right")
    if i1 - i0 > 5:
        grid = np.interp(t - np.arange(30, -1, -1.0), ts[i0:i1], v[i0:i1])
        f["f_vol30"] = float(np.std(np.diff(np.log(grid))) * 1e4)
        j0 = np.searchsorted(ts, t - 3.0)
        w = side * v[j0:i1]
        f["f_onset"] = float(t - ts[j0 + int(np.argmin(w))]) if len(w) else 3.0   # since the opposite extreme
    else:
        f["f_vol30"], f["f_onset"] = np.nan, np.nan
    g = c.g(t)
    blk = c.rsz[max(0, g - 200):g + 1][:, cols[:s_idx + 6]]
    k0, k1 = np.searchsorted(c.tr_t, t - 1.0), np.searchsorted(c.tr_t, t, "right")
    f["f_cancel_1"] = max(float(np.maximum(-np.diff(blk, axis=0), 0).sum()) - float(c.tr_sz[k0:k1].sum()), 0.0)
    f["f_hour"] = (t % 86400) / 3600
    f["f_lag"] = (t - o.t_venue) if o.t_venue == o.t_venue else -1.0
    f["f_src"] = {"pb": 0, "sb": 1, "pm": 2}.get(o.src, 3)
    f["f_edge"], f["f_value"] = o.edge, o.value
    f["f_pred_opp"] = min(o.pred_up, o.pred_dn)
    fp = o.fair_p if side > 0 else 1 - o.fair_p
    f["f_fair_edge"] = fp - o.seen
    f["f_left"] = o.end - t
    return f
