"""Recorded hours (data/live, or a paper run's raw/ directory: same format) as one
time-ordered event stream, parsed with the live parsers (feeds/parse.py).

`quantize=True` moves each Polymarket message to the research book grid (receipt time
rounded up to the next 5 ms step from start - 2 s, research/strategy/sim/grid.py), so a
replay reads the book exactly as the offline tables do; the live bot never quantizes."""
from __future__ import annotations

import gzip
import heapq
import json
import math
import zlib
from pathlib import Path
from typing import Iterator

from ..feeds import parse

DT = 0.005
LIVE = Path(__file__).resolve().parents[3] / "data" / "live"


def lines(root: Path, stream: str, hours) -> Iterator[tuple[float, str]]:
    for h in hours:
        for p in sorted(root.glob(f"*/{stream}-{h}.tsv.gz")):
            try:
                with gzip.open(p, "rt") as fh:
                    for line in fh:
                        t, _, raw = line.rstrip("\n").partition("\t")
                        if raw:
                            yield int(t) / 1e9, raw
            except (EOFError, zlib.error, gzip.BadGzipFile):
                continue


def markets(root: Path, hours, fam: str = "5m") -> dict[str, dict]:
    out = {}
    for t, raw in lines(root, "markets", hours):
        m = json.loads(raw)
        if m.get("fam") == fam:
            out.setdefault(m["slug"], dict(m, seen_t=t))
    return out


def grid_ceil(t: float, t0: float) -> float:
    """Next grid step at or after t; messages before the grid start keep their time (the
    offline book folds them into its first row, which ends in the same state)."""
    return t0 + math.ceil((t - t0) / DT - 1e-9) * DT if t > t0 else t


def _binance(root, hours, perp: bool):
    seen = set()
    for t, raw in lines(root, "binance_fut" if perp else "binance", hours):
        ev, key = parse.binance(t, raw, perp)
        if ev is None or key in seen:
            continue
        seen.add(key)
        if len(seen) > 200_000:
            seen.clear()
        yield ev


def _clob(root, hours, mk: dict, quantize: bool):
    """quantize: messages of one market landing on the same grid step are merged into one
    event (a full book becomes a (0, 0, 0) marker), so the top is read once per step as
    the offline grid does."""
    ups = {m["up"]: s for s, m in mk.items()}
    held = None
    for t, raw in lines(root, "clob_5m", hours):
        for ev in parse.clob(t, raw, ups):
            if not quantize:
                yield ev
                continue
            tq = grid_ceil(t, mk[ev[3]]["start"] - 2)
            chg = ([(0, 0, 0.0)] if ev[4] else []) + ev[5]
            if held is not None and held[1] == tq and held[3] == ev[3]:
                held[5].extend(chg)
                held[2] = ev[2]
                continue
            if held is not None:
                yield tuple(held)
            held = ["pm", tq, ev[2], ev[3], False, chg]
    if held is not None:
        yield tuple(held)


def events(root: Path, hours, quantize: bool = False, mk: dict | None = None) -> Iterator[tuple]:
    """Merged stream: ("mk", t, meta) rows first at their subscribe time, then every event."""
    mk = mk if mk is not None else markets(root, hours)
    rows = sorted((("mk", m["seen_t"], m) for m in mk.values()), key=lambda e: e[1])
    srcs = [iter(rows), _binance(root, hours, False), _binance(root, hours, True),
            _clob(root, hours, mk, quantize)]
    return heapq.merge(*srcs, key=lambda e: e[1])
