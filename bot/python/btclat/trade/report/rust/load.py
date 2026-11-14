"""Read a run directory of btl_log files into per-kind frames.

Accepts `<prefix>-*.jsonl` and `.jsonl.gz`, tolerates a truncated last line and a gzip cut
without its trailer (a killed process), drops exact duplicates (a crash between writing the .gz
and removing the plain file) and returns events sorted by (run start, run, seq)."""
from __future__ import annotations

import json
import zlib
from pathlib import Path
from typing import Iterator

import pandas as pd

PREFIX = "bot"


def _gz_lines(path: Path) -> Iterator[bytes]:
    """Inflate by hand so every byte before a cut (no trailer, torn block) is still returned;
    gzip.open can lose the final buffered chunk when it hits EOFError."""
    d, tail = zlib.decompressobj(31), b""
    with open(path, "rb") as fh:
        while chunk := fh.read(1 << 16):
            try:
                while chunk:
                    tail += d.decompress(chunk)
                    chunk = d.unused_data
                    if d.eof and chunk:        # another gzip member follows
                        d = zlib.decompressobj(31)
            except zlib.error:
                break
            *lines, tail = tail.split(b"\n")
            yield from lines
    yield from tail.split(b"\n")              # a torn last line fails json.loads and is skipped


def _raw_lines(path: Path) -> Iterator[bytes]:
    try:
        if path.suffix == ".gz":
            yield from _gz_lines(path)
        else:
            with open(path, "rb") as fh:
                yield from fh
    except OSError:
        return


def files(run_dir: Path, prefix: str = PREFIX) -> list[Path]:
    return sorted([*run_dir.glob(f"{prefix}-*.jsonl"), *run_dir.glob(f"{prefix}-*.jsonl.gz")])


def events(run_dir: Path, prefix: str = PREFIX) -> list[dict]:
    seen, out = set(), []
    for p in files(run_dir, prefix):
        for raw in _raw_lines(p):
            try:
                e = json.loads(raw)
            except ValueError:
                continue  # truncated last line
            if not isinstance(e, dict) or "kind" not in e or "seq" not in e:
                continue
            key = (e.get("run"), e["seq"], e.get("mono_ns"), e.get("wall_ns"))
            if key in seen:
                continue
            seen.add(key)
            out.append(e)
    first = {}
    for e in out:
        first[e.get("run")] = min(first.get(e.get("run"), e.get("wall_ns") or 0), e.get("wall_ns") or 0)
    out.sort(key=lambda e: (first[e.get("run")], str(e.get("run")), e["seq"]))
    return out


def frames(run_dir: Path, prefix: str = PREFIX) -> dict[str, pd.DataFrame]:
    """One DataFrame per event kind (columns = union of the kind's fields)."""
    by: dict[str, list[dict]] = {}
    for e in events(run_dir, prefix):
        by.setdefault(e["kind"], []).append(e)
    return {k: pd.DataFrame(v) for k, v in by.items()}


def get(fr: dict[str, pd.DataFrame], kind: str) -> pd.DataFrame:
    return fr.get(kind, pd.DataFrame())
