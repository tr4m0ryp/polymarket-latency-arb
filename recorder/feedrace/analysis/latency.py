"""(c) Venue time to local receipt per stream: wall_recv - venue stamp, in ms.

The box clock is chrony-disciplined (Amazon Time Sync); chrony.tsv gives its offset, which is
reported and is ~us, far below the ms figures. Venue clocks are taken as true UTC. Stamps:
Binance E (push) and T (match); Bybit ts (push) and cts / trade T (match); OKX ts; Coinbase time.
Millisecond venue stamps truncate, so those figures read ~0.5 ms high."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from ids import q

KIND = {0: "trade", 1: "book", 2: "depth"}


def chrony(run: Path) -> dict:
    off = []
    for ln in (run / "chrony.tsv").read_text().splitlines():
        f = ln.split("\t")[2].split(",")
        if len(f) > 5:
            try:
                off.append(abs(float(f[4])) * 1e6)  # CSV field 5: system time offset, s
            except ValueError:
                pass
    return {"abs_offset_us": q(off, (50, 99)), "max_abs_offset_us": max(off, default=None)}


def stream(run: Path, name: str) -> dict:
    from parse import load
    d = load(run, name)
    out = {}
    for k, kn in KIND.items():
        m = d["kind"] == k
        if not m.any():
            continue
        for col, lab in (("vts", "push"), ("vts2", "match")):
            v = d[col][m]
            ok = v > 0
            if ok.sum() > 10:
                lat = d["wall"][m][ok] / 1e6 - v[ok] / 1e3
                out[f"{kn}_{lab}_to_recv_ms"] = q(lat, (10, 50, 90, 99))
        if k != 2 and "trade_push_to_recv_ms" in out and k == 0:
            v1, v2 = d["vts"][m], d["vts2"][m]
            ok = (v1 > 0) & (v2 > 0)
            if ok.sum() > 10:
                out["trade_push_minus_match_ms"] = q((v1[ok] - v2[ok]) / 1e3, (50, 90, 99))
    return out
