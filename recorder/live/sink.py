"""Append-only, hour-rotated gzip logs: one line per message,
`<recv_ns>\\t<raw message>`. recv_ns is the SNTP-corrected receipt time."""
from __future__ import annotations

import gzip
import threading
import time
import zlib
from collections import deque
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parents[2] / "data" / "live"
OPEN: list["Sink"] = []  # every sink, so shutdown can close (and flush) them all


def _writer_loop(every: float = 0.5) -> None:
    """Compression and disk I/O run here, off the event loop: a busy loop got
    the CLOB socket closed for 'slow consumer' 14 times in the first 4 h run."""
    while True:
        time.sleep(every)
        for s in list(OPEN):
            s.drain()


threading.Thread(target=_writer_loop, daemon=True, name="sink-writer").start()


class Sink:
    def __init__(self, name: str, root: Path = ROOT, flush_s: float = 5.0) -> None:
        self.name, self.root, self.flush_s = name, root, flush_s
        self.hour, self.fh, self.last_flush, self.n = None, None, 0.0, 0
        self.buf: deque[tuple[int, str]] = deque()
        self.lock = threading.Lock()
        OPEN.append(self)

    def _open(self, hour: int) -> None:
        if self.fh:
            self.fh.close()
        day = time.strftime("%Y-%m-%d", time.gmtime(hour * 3600))
        d = self.root / day
        d.mkdir(parents=True, exist_ok=True)
        self.fh = gzip.open(d / f"{self.name}-{hour}.tsv.gz", "at", compresslevel=3)
        self.hour = hour

    def write(self, recv_ns: int, raw: str) -> None:
        """Cheap, called on the event loop: queue only."""
        self.buf.append((recv_ns, raw))
        self.n += 1

    def drain(self) -> None:
        with self.lock:
            while self.buf:
                recv_ns, raw = self.buf.popleft()
                hour = recv_ns // 3_600_000_000_000
                if hour != self.hour or self.fh is None:
                    self._open(hour)
                self.fh.write(f"{recv_ns}\t{raw.replace(chr(10), ' ')}\n")
            now = time.monotonic()
            if self.fh and now - self.last_flush > self.flush_s:
                self.fh.flush()
                self.last_flush = now

    @staticmethod
    def close_all() -> None:
        for s in list(OPEN):
            OPEN.remove(s)  # the writer thread stops draining it
            s.close()

    def close(self) -> None:
        self.drain()
        with self.lock:
            if self.fh:
                self.fh.close()
                self.fh = None


def read_stream(name: str, root: Path = ROOT) -> Iterator[tuple[int, str]]:
    """Every (recv_ns, raw) of a stream in time order; tolerates a file cut
    mid-write by a kill (gzip without trailer)."""
    for p in sorted(root.glob(f"*/{name}-*.tsv.gz"), key=lambda p: int(p.stem.split("-")[-1].split(".")[0])):
        try:
            with gzip.open(p, "rt") as fh:
                for line in fh:
                    t, _, raw = line.rstrip("\n").partition("\t")
                    if raw:
                        yield int(t), raw
        except (EOFError, zlib.error, gzip.BadGzipFile):
            continue
