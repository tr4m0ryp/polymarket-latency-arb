"""Hedged requests: one request (same body, same L2 headers) sent at once on k warm HTTP/2
sessions (own TCP + TLS each, own Cloudflare edge connection); the first good answer wins.

The duplicate-send test (hold/dup.py) showed the venue keeps ONE order per signed payload on
2-3 connections and cuts the ack p90 from 334 to 45 ms; a cancel is idempotent. Unlike
venue/fanout.py (a measurement: barrier, waits for every copy) a hedged send returns at the
first good copy; the rest finish in the pool and are reported through `when_all`."""
from __future__ import annotations

import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

from ...venue import parse
from ...venue.http import Http

LATE = ("transport", "duplicate", "timeout", "engine_restart")


class Hedge:
    def __init__(self, now_ns, k: int, sessions: list | None = None, per_op: int = 4):
        if not 1 <= k <= 3:
            raise ValueError(f"hedge k={k} outside 1..3")
        self.sessions = sessions or [Http(now_ns) for _ in range(k)]
        self.pool = ThreadPoolExecutor(max_workers=per_op * len(self.sessions), thread_name_prefix="hedge")

    @property
    def k(self) -> int:
        return len(self.sessions)

    def send(self, method: str, path: str, headers: dict, body: str | None, good) -> tuple:
        """(the first response `good` accepts, else the most telling bad one; every copy's future)."""
        futs = [self.pool.submit(s.req, method, path, headers, body) for s in self.sessions]
        pending = set(futs)
        while pending:
            done, pending = wait(pending, return_when=FIRST_COMPLETED)
            for f in done:
                if good(f.result()):
                    return f.result(), futs
        rs = [f.result() for f in futs]
        told = [r for r in rs if parse.classify(r.code, r.body) not in LATE]
        return (told or rs)[0], futs

    def warm(self, idle_s: float = 1.0) -> list[float]:
        """GET /time on each session idle for >= idle_s (an idle connection costs +20-40 ms)."""
        out = []
        for s in self.sessions:
            if s.last is None or time.monotonic() - s.last >= idle_s:
                out.append(round(s.req("GET", "/time").ms, 3))
        return out

    def close(self) -> None:
        self.pool.shutdown(wait=True)
        for s in self.sessions:
            s.close()


def when_all(futs: list, fn) -> None:
    """fn(responses) once every copy has its response (called on the last copy's thread)."""
    left, lock = [len(futs)], threading.Lock()

    def one(_):
        with lock:
            left[0] -= 1
            last = left[0] == 0
        if last:
            fn([f.result() for f in futs])
    for f in futs:
        f.add_done_callback(one)


def copies(rs: list) -> list[dict]:
    return [{"code": r.code, "ms": round(r.ms, 3), "t_send_ns": r.t_send_ns, "t_ack_ns": r.t_ack_ns,
             "pop": r.hdr.get("cf-ray", "-").split("-")[-1], "err_kind": parse.classify(r.code, r.body),
             "err": r.err} for r in rs]
