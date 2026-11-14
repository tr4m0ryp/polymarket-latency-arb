"""Order ops through the sender process (child.py): the event loop only pickles the quote's
fields into a pipe; signing, the hedged POST / DELETE and the venue's answer happen in the
child. Results come back on the same loop (loop.add_reader on the pipe: no thread hop).
Lookups, balance and trade reads stay in this process (LiveOps): they are not on the clock.

`mode`: "proc" sends every insert / cancel through the child; "ab" picks child or the
in-process pool (LiveOps) at random per op, so one run measures both on the same decisions
(`via` on every ack). Fail closed: if the child dies, every op in flight answers `unknown`
(the manager stops, the session's cancel-all follows) and later ops are refused the same way."""
from __future__ import annotations

import itertools
import multiprocessing as mp
import random

from ..ops.live import LiveOps
from . import child

FIELDS = ("cid", "token", "price", "size", "otype", "expiration", "oid")
DEAD = {"ok": False, "confirmed": False, "unknown": True}


class RemoteOps(LiveOps):
    def __init__(self, venue, hedge, post, note, loop, spec: dict, mode: str = "proc", seed: int | None = None,
                 start_s: float = 30.0):
        if mode not in ("proc", "ab"):
            raise ValueError(f"sender mode {mode!r}")
        super().__init__(venue, hedge, post, note)
        self.loop, self.mode, self.rng = loop, mode, random.Random(seed)
        ctx = mp.get_context("spawn")             # never fork a process that runs threads
        self.conn, theirs = ctx.Pipe(duplex=True)
        self.proc = ctx.Process(target=child.serve, args=(theirs, spec), daemon=True, name="maker-sender")
        self.proc.start()
        theirs.close()
        if not self.conn.poll(start_s):
            self.proc.kill()
            raise RuntimeError(f"sender process not ready within {start_s} s")
        msg = self.conn.recv()
        if msg[0] != "ready":
            raise RuntimeError(f"sender process said {msg!r}")
        self.pid, self.dead = msg[1], None
        self.seq = itertools.count()
        self.pending: dict[int, tuple] = {}
        self.wait_copies: dict[int, tuple] = {}
        self.warm_ms: list[float] = []
        self.n_via = {"proc": 0, "thread": 0}
        loop.add_reader(self.conn.fileno(), self._readable)

    # routing -------------------------------------------------------------------------------
    def _route(self) -> str:
        via = "proc" if self.mode == "proc" or self.rng.random() < 0.5 else "thread"
        self.n_via[via] += 1
        return via

    def insert(self, o, cb) -> None:
        if self._route() == "thread":
            return super().insert(o, lambda res: cb({**res, "via": "thread"}))
        self._send("insert", o, cb)

    def cancel(self, o, cb) -> None:
        if self._route() == "thread":
            return super().cancel(o, lambda res: cb({**res, "via": "thread"}))
        self._send("cancel", o, cb)

    def _send(self, kind: str, o, cb) -> None:
        if self.dead:
            cb({**DEAD, "exc": self.dead, "via": "proc"})
            return
        rid = next(self.seq)
        self.pending[rid] = (kind, o, cb)
        try:
            self.conn.send((kind, rid, {k: getattr(o, k, None) for k in FIELDS}))
        except (OSError, ValueError) as e:
            self._die(f"sender pipe: {e!r}"[:200])

    # answers (on the loop) -----------------------------------------------------------------
    def _readable(self) -> None:
        try:
            while self.conn.poll():
                self._on(self.conn.recv())
        except (EOFError, OSError) as e:
            self._die(f"sender process gone: {e!r}"[:200])

    def _on(self, msg) -> None:
        if msg[0] == "res":
            kind, o, cb = self.pending.pop(msg[1])
            self.wait_copies[msg[1]] = (kind, o)
            cb(msg[2])
        elif msg[0] == "copies":
            kind, o = self.wait_copies.pop(msg[1], (None, None))
            if o is not None:
                self.note("copies", what=kind, cid=o.cid, oid=o.oid, copies=msg[2], via="proc")
        elif msg[0] == "warm":
            self.warm_ms = msg[1]

    def _die(self, why: str) -> None:
        if self.dead:
            return
        self.dead = why
        self.note("sender_dead", err=why)
        try:
            self.loop.remove_reader(self.conn.fileno())
        except (ValueError, OSError):
            pass
        for kind, o, cb in self.pending.values():
            cb({**DEAD, "exc": why, "via": "proc"})
        self.pending.clear()

    # housekeeping --------------------------------------------------------------------------
    def set_offset(self, offset_ns: int) -> None:
        if not self.dead:
            try:
                self.conn.send(("clock", int(offset_ns)))
            except (OSError, ValueError) as e:
                self._die(f"sender pipe: {e!r}"[:200])

    def keep_warm(self) -> list[float]:
        """The in-process sessions only serve the A/B arm; the child keeps its own warm."""
        if self.mode == "ab":
            return super().keep_warm()
        ms, self.warm_ms = self.warm_ms, []
        return ms

    def detach(self) -> None:
        """On the loop, before close(): stop reading the pipe."""
        try:
            self.loop.remove_reader(self.conn.fileno())
        except (ValueError, OSError):
            pass

    def close(self) -> None:
        try:
            self.conn.send(("close",))
        except (OSError, ValueError):
            pass
        self.proc.join(10)
        if self.proc.is_alive():
            self.proc.kill()
        self.conn.close()
        super().close()
