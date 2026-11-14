"""Does a venue's BTC move predict the Polymarket 5m ask move, and does it arrive before it?

Side ask: the Up ask after an up move, the Down ask after a down move (the side that reprices up).
reprice = first PM update after the reference time where that ask is >= 1 c above its value at
the reference time. All times are local receipt (CLOCK_MONOTONIC) on the same box.
  own onsets  every onset of a signal (move.onsets at X): hit = side ask reprices within 1 s;
              `base` = the same for random times and directions (chance level)
  per move    market-wide moves (move.market_moves): reprice after the first venue onset;
              per signal, reprice - signal onset (> 0: the signal arrived before PM repriced)
Skips the first 10 s and last 15 s of each market and asks outside 0.05-0.95."""
from __future__ import annotations

import numpy as np

from ids import q
from moves import market_moves, onsets
from parse import load

HIT_NS, TICK = 1_000_000_000, 0.0099


class Book:
    def __init__(self, run):
        d = load(run, "pm")
        c = load(run, "spot_comb_a")
        self.off = int(np.median(c["wall"] - c["mono"]))
        self.s = {}
        for k in (1, 3):
            m = d["kind"] == k
            for st in np.unique(d["key2"][m]):
                mm = m & (d["key2"] == st)
                o = np.argsort(d["mono"][mm], kind="stable")
                self.s[(k, int(st))] = (d["mono"][mm][o], d["px"][mm][o])

    def reprice(self, t: int, direction: int) -> tuple[float | None, bool]:
        """(ns from t to the side ask's +1 c reprice or None, usable)"""
        wall_s = (t + self.off) / 1e9
        st = int(wall_s // 300 * 300)
        if not 10 <= wall_s - st <= 285 or (1 if direction > 0 else 3, st) not in self.s:
            return None, False
        tt, aa = self.s[(1 if direction > 0 else 3, st)]
        i = np.searchsorted(tt, t, side="right") - 1
        if i < 0 or not 0.05 <= aa[i] <= 0.95:
            return None, False
        up = np.flatnonzero(aa[i + 1:] >= aa[i] + TICK)
        return (float(tt[i + 1 + up[0]] - t) if len(up) else None), True


def own(book: Book, sigs: dict, x: float, seed: int = 0) -> dict:
    out = {}
    for n, (t, p) in sigs.items():
        res = [book.reprice(tm, d) for tm, d in onsets(t, p, x)]
        dl = [r for r, ok in res if ok]
        hits = [r is not None and r <= HIT_NS for r in dl]
        out[n] = {"onsets": len(dl), "hit_1s": round(float(np.mean(hits)), 3) if dl else None,
                  "reprice_after_onset_ms": q([r / 1e6 for r in dl if r is not None and r <= HIT_NS])}
    rng = np.random.default_rng(seed)
    t_all = sigs["BASE_spot_comb_a"][0]
    rnd = [book.reprice(int(tm), int(d)) for tm, d in zip(rng.integers(t_all[0], t_all[-1], 4000),
                                                         rng.choice([-1, 1], 4000))]
    dl = [r for r, ok in rnd if ok]
    out["base_random"] = {"onsets": len(dl), "hit_1s": round(float(np.mean(
        [r is not None and r <= HIT_NS for r in dl])), 3) if dl else None}
    return out


def per_move(book: Book, sigs: dict, x: float, names: list[str]) -> dict:
    moves, venue = market_moves(sigs, x)
    out = {n: [] for n in names}
    used = 0
    for m in moves:
        t0 = min(m["on"][v] for v in venue if v in m["on"])
        r, ok = book.reprice(t0, m["dir"])
        if not ok or r is None or r > 2 * HIT_NS:
            continue
        used += 1
        for n in names:
            if n in m["on"]:
                out[n].append((t0 + r - m["on"][n]) / 1e6)
    return {"moves_with_reprice": used, **{n: {**q(v, (10, 25, 50, 75, 90)), "before_pm_share": round(
        float(np.mean([a > 0 for a in v])), 3) if v else None} for n, v in out.items()}}
