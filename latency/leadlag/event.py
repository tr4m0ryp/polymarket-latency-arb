"""Per-market event study: Binance burst -> Polymarket Up-book reaction.

For each burst onset (Binance server time T0, our receipt R0) inside a live
market: the first reprice of the Up book in the burst's direction (lag on our
receipt clock and on the venues' server clocks), whether a trade or a requote
moved it, and the stale depth: shares the book still offers at a price that
beats fair after the move net of the taker fee, and how much of it survives
0-5 s after R0 (what a bot reacting that late could still take)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import book
import spot

OFFS = (0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0)
PROF = (-1.0, -0.5, -0.25, 0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0)  # catch-up profile
PRE, EXPOST = 1.2, 3.0  # reference mid before the move; ex-post fair = mid 3 s after R0
CENSOR = 10.0


def _first_move(top: pd.DataFrame, r0: float, d: float, bb0: float, ba0: float):
    t = top["t"].to_numpy()
    i = np.searchsorted(t, r0, side="right")
    j = np.searchsorted(t, r0 + CENSOR, side="right")
    bb, ba = top["bb"].to_numpy()[i:j], top["ba"].to_numpy()[i:j]
    hit = (bb > bb0 + 1e-9) | (ba > ba0 + 1e-9) if d > 0 else (ba < ba0 - 1e-9) | (bb < bb0 - 1e-9)
    k = np.flatnonzero(hit)
    return (np.nan, np.nan) if not len(k) else (t[i + k[0]], top["ts"].to_numpy()[i + k[0]])


def _stale(snap, d: float, fair: float) -> dict[float, tuple[float, float]]:
    """price -> (shares, edge per share) of levels a taker could buy profitably."""
    bids, asks = snap
    out = {}
    if d > 0:  # buy Up at the ask
        for p, s in asks.items():
            e = fair - p - spot.fee(p)
            if e > 0:
                out[p] = (s, e)
    else:  # buy Down = hit Up bids; Down price 1 - p
        for p, s in bids.items():
            e = p - fair - spot.fee(1 - p)
            if e > 0:
                out[p] = (s, e)
    return out


MAX_BN_LAG, MAX_CLOB_LAG = 0.3, 0.1  # our receipt backlog limits (s) for a clean event


def study(m: dict, rows: pd.DataFrame, tr: pd.DataFrame, ev: pd.DataFrame,
          gaps: list[tuple[float, float]] = ()) -> pd.DataFrame:
    """ev: DataFrame T0, R0, d, s_before, s_after (bursts or random baseline times)."""
    k = spot.strike(tr, m["start"])
    lo, hi = max(m["start"], rows["t"].min() + 2), m["end"] - 30
    ev = ev[(ev["R0"] > lo) & (ev["R0"] < hi)].reset_index(drop=True)
    if not len(ev) or np.isnan(k):
        return pd.DataFrame()
    q = np.concatenate([ev["R0"].to_numpy() + o for o in OFFS])
    rt, rp = tr.sort_values("t")["t"].to_numpy(), tr.sort_values("t")["px"].to_numpy()
    top, snaps = book.replay(rows, m["up"], q)
    order = np.argsort(q, kind="stable")
    snap_at = {}
    for rank, qi in enumerate(order):
        snap_at[qi] = snaps[rank]
    tk = rows[rows["kind"] == 2]
    trades = tk["t"].to_numpy()
    rt_all, rlag = rows["t"].to_numpy(), (rows["t"] - rows["ts"]).to_numpy()
    t_up = (tk["asset"] == m["up"]).to_numpy()
    t_pu = np.where(t_up, tk["price"].to_numpy(), 1 - tk["price"].to_numpy())  # Up-frame price
    t_dir = np.where(t_up, 1, -1) * tk["side"].to_numpy()  # +1: taker bought Up exposure
    t_sz = tk["size"].to_numpy()
    out = []
    n = len(ev)
    for e in ev.itertuples():
        bb0, ba0 = book.top_at(top, np.array([e.R0]))
        bbm, bam = book.top_at(top, np.array([e.R0 - PRE]))
        bb0, ba0, bbm, bam = bb0[0], ba0[0], bbm[0], bam[0]
        if np.isnan(bb0) or np.isnan(ba0) or np.isnan(bbm) or np.isnan(bam):
            continue
        t1, ts1 = _first_move(top, e.R0, e.d, bb0, ba0)
        took = bool(len(trades)) and np.any((trades > t1 - 0.15) & (trades < t1 + 0.05))
        sig = spot.sigma_1s(tr, e.T0)
        tau = m["end"] - e.T0
        dfair = (spot.p_up(np.array([e.s_after]), k, sig, tau)
                 - spot.p_up(np.array([e.s_before]), k, sig, tau))[0]
        mid_pre = (bbm + bam) / 2
        pb, pa = book.top_at(top, e.R0 + np.array(PROF))
        bpx = rp[np.clip(np.searchsorted(rt, e.R0 + np.array(PROF + (-PRE,)), side="right") - 1, 0, None)]
        fairs = {"mdl": mid_pre + dfair, "mo": (pb + pa)[PROF.index(EXPOST)] / 2}
        a, b = np.searchsorted(rt_all, [e.R0 - 1.0, e.R0 + 1.0])
        clob_lag = float(np.nanmedian(rlag[a:b])) if b > a else np.nan
        in_gap = any(g0 - 5 < e.R0 < g1 + 5 for g0, g1 in gaps)
        row = {"slug": m["slug"], "bn_lag": e.R0 - e.T0, "clob_lag": clob_lag,
               "ok": (e.R0 - e.T0 <= MAX_BN_LAG) and clob_lag <= MAX_CLOB_LAG and not in_gap, "fam": m["fam"], "T0": e.T0, "R0": e.R0, "d": e.d,
               "move_bp": e.move_bp, "dfair": dfair, "mid_pre": mid_pre,
               "pre_moved": (bb0 > bbm or ba0 > bam) if e.d > 0 else (bb0 < bbm or ba0 < bam),
               "lag_recv": t1 - e.R0, "lag_server": ts1 - e.T0, "by_trade": took,
               "spread0": ba0 - bb0, "secs_left": m["end"] - e.T0}
        for o, b, a, x in zip(PROF, pb, pa, bpx[:-1]):
            row[f"dmid_{o:g}"] = e.d * ((b + a) / 2 - mid_pre)
            row[f"dbn_{o:g}"] = e.d * 1e4 * np.log(x / bpx[-1])  # Binance on our receipt clock
        w = (trades >= e.R0 - 0.5) & (trades <= e.R0 + 2.0) & (t_dir == e.d)
        pu, sz = t_pu[w], t_sz[w]
        paid = pu if e.d > 0 else 1 - pu
        row["taken_usd"] = float((sz * paid).sum())
        row["taken_edge"] = float((sz * (e.d * (fairs["mo"] - pu) - spot.fee(paid))).sum())
        row["taken_n"] = int(w.sum())
        row["against_usd"] = float((t_sz * np.where(t_dir > 0, t_pu, 1 - t_pu))[
            (trades >= e.R0 - 0.5) & (trades <= e.R0 + 2.0) & (t_dir == -e.d)].sum())
        for fk, fair in fairs.items():
            base = _stale(snap_at[e.Index], e.d, fair)
            for oi, o in enumerate(OFFS):
                bids, asks = snap_at[oi * n + e.Index]
                book_now = asks if e.d > 0 else bids
                usd = edge = 0.0
                for p, (s0, ed) in base.items():
                    s = min(s0, book_now.get(p, 0.0))
                    usd += s * (p if e.d > 0 else 1 - p)
                    edge += s * ed
                row[f"{fk}_usd_{o:g}"], row[f"{fk}_edge_{o:g}"] = usd, edge
        out.append(row)
    return pd.DataFrame(out)
