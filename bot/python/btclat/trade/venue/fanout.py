"""Identical-copy sends: one signed order POSTed at the same instant on k separate HTTP/2
sessions (own TCP + TLS each, so own Cloudflare edge connection), first ack wins.

Only safe if the venue dedupes copies by order hash (one order, the rest "duplicated");
hold/dup.py measures exactly that with unfillable orders before anything relies on it. Each
copy carries the same body and the same L2 headers (same timestamp and HMAC)."""
from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor

from .http import Http

MAX_CONNS = 3


class Fanout:
    def __init__(self, venue, k: int = MAX_CONNS, sessions: list | None = None):
        if not 1 <= k <= MAX_CONNS:
            raise ValueError(f"fanout k={k} outside 1..{MAX_CONNS}")
        self.venue = venue
        self.sessions = sessions or [Http(venue.http.now_ns) for _ in range(k)]
        self.pool = ThreadPoolExecutor(max_workers=len(self.sessions))

    def warm(self) -> list[float]:
        """One GET /time per session (TLS set up, connection warm), round trips in ms."""
        return [round(s.req("GET", "/time").ms, 3) for s in self.sessions]

    def post(self, signed, k: int) -> list:
        """The same signed order on the first k sessions, released together by a barrier."""
        if not 1 <= k <= len(self.sessions):
            raise ValueError(f"k={k} outside 1..{len(self.sessions)}")
        headers = self.venue.post_headers(signed)
        gate = threading.Barrier(k)

        def one(s):
            gate.wait(timeout=5)
            return s.req("POST", "/order", headers=headers, body=signed.body)
        futs = [self.pool.submit(one, s) for s in self.sessions[:k]]
        return [f.result() for f in futs]

    def close(self) -> None:
        self.pool.shutdown(wait=True)
        for s in self.sessions:
            s.close()
