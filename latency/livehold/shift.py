"""How much earlier would the match need to be? Replay each order at M - delta.

Same limit as live, same 10 s markout, the match instant moved earlier by delta (what a faster
feed, network or a shorter hold would buy). Also times when the depth at our limit vanished.

    PYTHONPATH=. python3 -m latency.livehold.shift"""
from __future__ import annotations

import pickle

import numpy as np
import pandas as pd

from research.predict.report.md import md
from . import OUT, TAPE
from .orders import load
from .replay import Replay
from .run import boot
from .sweep import ACK_AFTER_MATCH, _fee, _mid, sweep

DELTAS_MS = (0, 30, 60, 100, 150, 200, 230)


def _pull_time(o, ev):
    """First venue time after send when depth <= limit drops below our size (None if not in 1 s)."""
    r = Replay(ev)
    r.at(o.t_send)
    for t, _, _ in ev:
        if t <= o.t_send:
            continue
        if t > o.t_send + 1.0:
            return None
        _, a = r.at(t)
        if sum(s for p, s in a.items() if p <= o.limit + 1e-9) < o.size:
            return t
    return None


def main():
    o = load()
    st = pickle.loads((TAPE / "streams.pkl").read_bytes())
    rows, pulls = [], []
    for x in o.itertuples():
        ev = st.get(x.token, [])
        M = x.t_ack - ACK_AFTER_MATCH
        tp = _pull_time(x, ev)
        pulls.append({"filled": x.filled, "pull_after_send_ms": None if tp is None else (tp - x.t_send) * 1e3,
                      "pull_after_event_ms": None if tp is None or x.t_event is None else (tp - x.t_event) * 1e3,
                      "send_after_event_ms": None if x.t_event is None else (x.t_send - x.t_event) * 1e3})
        for d in DELTAS_MS:
            r = Replay(ev)
            _, a = r.at(M - d / 1e3 - 0.001)
            sh, px = sweep(dict(a), x.limit, x.size)
            mid10 = _mid(r, M - d / 1e3 + 10.0)
            row = {"delta_ms": d, "sig": x.sig, "slug": x.slug, "fill_sh": sh, "px": px, "seen": x.seen}
            if sh > 0 and mid10 is not None:
                row.update(mk10_c=(mid10 - px - _fee(px)) / px * 100, pnl=sh * (mid10 - px - _fee(px)), cost=sh * px)
            rows.append(row)
    df, pu = pd.DataFrame(rows), pd.DataFrame(pulls)
    rng = np.random.default_rng(7)
    tab = []
    for d, g in df.groupby("delta_ms"):
        f = g[g["fill_sh"] > 0]
        est, lo, hi = boot(f, rng)
        tab.append({"match_earlier_ms": d, "fill_rate": len(f) / len(g), "mk10_c_per_$": est, "lo": lo, "hi": hi,
                    "usd_per_order": f["pnl"].sum() / len(g)})
    q = lambda s: np.nanpercentile(s.dropna(), [10, 25, 50, 75, 90]).round(0).tolist() if s.notna().any() else []
    m = pu[~pu["filled"]]
    txt = ["# Earlier match instant (live limit)\n", md(pd.DataFrame(tab), 2),
           "\n## When the depth at our limit vanished (orders that missed live), ms p10/25/50/75/90\n",
           f"- after our send: {q(m['pull_after_send_ms'])} (n {m['pull_after_send_ms'].notna().sum()} of {len(m)})",
           f"- after the venue event that triggered us (book-triggered only): {q(m['pull_after_event_ms'])}",
           f"- our send after that event: {q(m['send_after_event_ms'])}"]
    (OUT / "shift.md").write_text("\n".join(txt) + "\n")
    print("\n".join(txt))


if __name__ == "__main__":
    main()
