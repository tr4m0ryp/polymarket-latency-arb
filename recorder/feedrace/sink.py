"""Per-stream gzip sink, rotated every `rot_s` seconds of wall time so a crash loses little.

Line: `<mono_ns>\\t<wall_ns>\\t<payload>`; binary payloads are written as `x:<hex>`.
Writes are buffered in memory and flushed by the recorder's flush task, off the receipt path."""
from __future__ import annotations

import gzip
import time
from pathlib import Path


class Sink:
    def __init__(self, root: Path, name: str, rot_s: int = 900):
        self.root, self.name, self.rot_s = root, name, rot_s
        self.buf: list[str] = []
        self.fh = None
        self.slot = -1

    def add(self, mono: int, wall: int, msg: str | bytes) -> None:
        if isinstance(msg, bytes):
            msg = "x:" + msg.hex()
        self.buf.append(f"{mono}\t{wall}\t{msg}\n")

    def flush(self) -> None:
        slot = int(time.time()) // self.rot_s
        if slot != self.slot:
            self.close()
            self.slot = slot
            self.fh = gzip.open(self.root / f"{self.name}-{slot * self.rot_s}.tsv.gz", "at",
                                compresslevel=1)
        if self.buf:
            buf, self.buf = self.buf, []
            self.fh.write("".join(buf))

    def close(self) -> None:
        if self.fh:
            self.fh.close()
            self.fh = None
