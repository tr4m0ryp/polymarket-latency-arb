"""Per-order competition measurements around one simulated taker order (venue clock unless
noted). The order reaches the CLOB at ta = t + L, matches at tf = ta + 150 ms.

- hold_*: same-side rival prints with ts in (ta, tf] (they matched ahead of us, inside our
  hold); `_lim` = only at the levels our limit allowed; lead = matched to leader A / B fills.
- aft25 / aft100: same-side prints at our levels in (tf, tf + 25 ms] / (tf + 25, tf + 100 ms]
  (rivals right behind the simulator's assumed match time).
- dep_dec / dep_match: shares up to our limit at ta and at tf; hold_traded = same-side print
  volume at those levels in (ta, tf]; the rest of the drop is cancels (makers requoting).
- van50 / van100: of the shares the simulator gave us, how many were gone from the book
  50 / 100 ms after tf (taken or cancelled); tr50 / tr100 = the part a rival print explains.
- pre1 / pre1_all / ev1: receipt-clock activity in the last 1 s before the decision (same-side
  prints, all prints, book messages); dep_seen_r = shares at the seen price in our view at t.
  These are decision-time observables (no look-ahead) for the size rules."""
from __future__ import annotations

import numpy as np

from ..data.prints import window
from .taker import cols_for

LAG = 0.025   # a print's stamp trails its book update by up to ~20-30 ms (measured)


def order_stats(book, R, p, ev_t, d, j, rec, L: float, hold: float = 0.150) -> dict:
    t, side, lim = float(d["t"][j]), int(d["side"][j]), float(d["limit"][j])
    ta, tf = t + L, t + L + hold
    cols = cols_for(side, lim)
    seen_col = (100 + int(round(d["seen"][j] * 100))) if side > 0 else int(round((1 - d["seen"][j]) * 100))
    gd, gm = int(book.g_ceil(ta)), int(book.g_ceil(tf))
    h = window(p, side, ta, tf)
    hl = h[h["col"].isin(cols)]
    a25 = window(p, side, tf, tf + 0.025, cols)
    a100 = window(p, side, tf + 0.025, tf + 0.100, cols)
    s = {"hold_n": len(h), "hold_sz": float(h["size"].sum()), "hold_n_lim": len(hl),
         "hold_traded": float(hl["size"].sum()), "hold_lead": int((h["who"] != "").sum()),
         "hold_opp": len(window(p, -side, ta, tf)),
         "aft25": len(a25), "aft25_sz": float(a25["size"].sum()), "aft25_lead": int((a25["who"] != "").sum()),
         "aft100": len(a100), "aft100_sz": float(a100["size"].sum()),
         "dep_dec": float(book.size[gd, cols].sum()) if len(cols) else 0.0,
         "dep_match": float(book.size[gm, cols].sum()) if len(cols) else 0.0,
         "dep_seen_dec": float(book.size[gd, seen_col]), "dep_seen_match": float(book.size[gm, seen_col]),
         "dep_seen_r": float(R[int(book.g_floor(t)), seen_col])}
    tp = p["t"].to_numpy()
    a, b = np.searchsorted(tp, t - 1.0, "right"), np.searchsorted(tp, t, "right")
    w = p.iloc[a:b]
    s["pre1"], s["pre1_all"] = int((w["d"] == side).sum()), len(w)
    s["ev1"] = int(np.searchsorted(ev_t, t, "right") - np.searchsorted(ev_t, t - 1.0, "right"))
    for X in (0.05, 0.10):
        van = tr = 0.0
        qx = int(book.g_ceil(rec["tf"] + X))
        for c, x in rec["lv"]:
            v = max(0.0, x - float(book.size[gm:qx + 1, c].min()))
            y = float(window(p, side, rec["tf"], rec["tf"] + X + LAG, [c])["size"].sum())
            van, tr = van + v, tr + min(v, y)
        k = int(X * 1000)
        s[f"van{k}"], s[f"tr{k}"] = van, tr
    return s
