"""The sender process: a second interpreter (its own GIL, its own CPU) that signs and sends our
inserts and cancels on k warm HTTP/2 sessions, so neither the feeds' event loop nor the
recorder ever stands between a decision and the wire, or between the venue's answer and us.

Protocol on one duplex pipe (multiprocessing.Connection, pickled tuples):
  parent -> child  ("insert" | "cancel", rid, order fields)   ("clock", offset_ns)   ("close",)
  child -> parent  ("ready", pid)  ("res", rid, result)  ("copies", rid, [copy, ...])  ("warm", [ms])
The child's main thread only dispatches; each op runs on its own pool thread (ops never queue
behind each other), and a keep-warm thread pings any session idle >= WARM_IDLE_S. Results are
the same dicts the in-process LiveOps returns (ops/live.py insert_op / cancel_op), tagged
`via: proc`. Stamps use the parent's SNTP offset (`clock`)."""
from __future__ import annotations

import importlib
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

from ..ops.hedge import Hedge, copies, when_all
from ..ops.live import cancel_op, insert_op

WARM_EVERY_S, WARM_IDLE_S = 0.5, 1.0


def live_spec(venue, clock, k: int) -> dict:
    """What the child needs to rebuild the connected client: creds, L2 keys, clock offsets."""
    return {"factory": f"{__name__}:live_venue", "creds": venue.creds, "api": venue.api,
            "offset_s": venue.offset_s, "offset_ns": clock.offset_ns, "k": k}


def live_venue(spec: dict, now_ns):
    """The real CLOB client, rebuilt in the child from the parent's connected one (no network)."""
    from ...venue.client import LiveClob
    v = LiveClob(spec["creds"], now_ns=now_ns)
    v.api, v.offset_s, v.derived = spec["api"], spec["offset_s"], True
    return v, Hedge(now_ns, spec["k"])


def _build(spec: dict, now_ns):
    mod, fn = spec["factory"].split(":")
    return getattr(importlib.import_module(mod), fn)(spec, now_ns)


def serve(conn, spec: dict) -> None:
    off = [int(spec.get("offset_ns") or 0)]

    def now_ns() -> int:
        return time.time_ns() + off[0]
    venue, hedge = _build(spec, now_ns)
    lock, stop = threading.Lock(), threading.Event()

    def send(msg) -> None:
        with lock:
            try:
                conn.send(msg)
            except (OSError, ValueError):      # parent gone: nothing left to tell
                stop.set()

    def job(kind: str, rid: int, o) -> None:
        try:
            res, futs = (insert_op if kind == "insert" else cancel_op)(venue, hedge, o)
        except Exception as e:  # a failed op is a result the manager acts on
            res, futs = {"ok": False, "confirmed": False, "unknown": True, "exc": repr(e)[:300]}, []
        send(("res", rid, {**res, "via": "proc"}))
        if futs:
            when_all(futs, lambda rs: send(("copies", rid, copies(rs))))

    def warm() -> None:
        while not stop.wait(spec.get("warm_s", WARM_EVERY_S)):
            try:
                ms = hedge.warm(WARM_IDLE_S)
            except Exception:  # a failed ping costs nothing; the next op reconnects
                ms = []
            if ms:
                send(("warm", ms))
    pool = ThreadPoolExecutor(max_workers=spec.get("workers", 6), thread_name_prefix="sender-op")
    threading.Thread(target=warm, daemon=True, name="sender-warm").start()
    hedge.warm(0.0)                                 # TLS up on every session before the first order
    send(("ready", os.getpid()))
    try:
        while not stop.is_set():
            try:
                msg = conn.recv()
            except (EOFError, OSError):
                break
            if msg[0] == "close":
                break
            if msg[0] == "clock":
                off[0] = int(msg[1])
            elif msg[0] in ("insert", "cancel"):
                pool.submit(job, msg[0], msg[1], SimpleNamespace(**msg[2]))
    finally:
        stop.set()
        pool.shutdown(wait=True)
        hedge.close()
        conn.close()
