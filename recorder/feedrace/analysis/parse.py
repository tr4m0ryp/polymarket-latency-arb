"""Parse a feed-race run into one NPZ per stream (cached under <run>/parsed/).

Columns (one row per trade print, top-of-book update or depth diff):
  mono, wall    receipt stamps, ns (CLOCK_MONOTONIC; chrony wall clock)
  kind          0 trade, 1 top of book (PM: Up ask), 2 depth diff, 3 PM Down ask
  key, key2     trade id / book update id (depth: last id u, first id U); -1 when absent
  px            trade price or book mid (USD)
  vts, vts2     venue stamps, us: Binance E / T, Bybit ts / cts or trade T, OKX ts, Coinbase time
Gzip files still being written are read up to their last complete block."""
from __future__ import annotations

import json
import zlib
from array import array
from pathlib import Path

import numpy as np

from parsers import parser

COLS = ("mono", "wall", "kind", "key", "key2", "px", "vts", "vts2")


def lines(path: Path):
    d, tail = zlib.decompressobj(31), b""
    with open(path, "rb") as fh:
        while chunk := fh.read(1 << 22):
            try:
                buf = tail + d.decompress(chunk)
            except zlib.error:
                break
            *full, tail = buf.split(b"\n")
            yield from full
            if d.eof:  # concatenated gzip members (appends)
                rest, d = d.unused_data, zlib.decompressobj(31)
                tail += d.decompress(rest) if rest else b""


def parse_stream(run: Path, name: str) -> Path:
    dst = run / "parsed" / f"{name}.npz"
    files = sorted(run.glob(f"{name}-*.tsv.gz"))
    if dst.exists() and dst.stat().st_mtime > max((f.stat().st_mtime for f in files), default=0):
        return dst
    f, st = parser(name), {"run": run}
    cols = {c: array("d" if c == "px" else "q") for c in COLS}
    put = [cols[c].append for c in COLS]
    for path in files:
        for ln in lines(path):
            parts = ln.split(b"\t", 2)
            if len(parts) < 3 or parts[2][:1] not in (b"{", b"["):
                continue
            a, b, msg = parts
            out: list = []
            try:
                f(json.loads(msg), out, st)
            except (ValueError, KeyError, TypeError, IndexError):
                continue  # torn tail of a file still being written, or an unexpected shape
            for r in out:
                for p_, v in zip(put, (int(a), int(b), *r)):
                    p_(v)
    arr = {c: np.frombuffer(cols[c], dtype=float if c == "px" else np.int64) for c in COLS}
    dst.parent.mkdir(exist_ok=True)
    np.savez(dst, **arr)
    return dst


def load(run: Path, name: str) -> dict:
    z = np.load(run / "parsed" / f"{name}.npz")
    return {c: z[c] for c in COLS}
