"""The single thread that owns the HTTP/2 session in micro mode: orders first, then keep-warm
`GET /time` whenever the queue has been idle `warm_s` (an idle connection costs +20-40 ms),
and a balance read every `balance_s`. One order at a time: `order()` returns False while an
order is queued or in flight, so the event loop never blocks and exposure stays exact."""
from __future__ import annotations

import queue
import threading
import time


class Worker(threading.Thread):
    def __init__(self, venue, warm_s: float = 1.0, balance_s: float = 60.0, on_balance=None, on_note=None):
        super().__init__(daemon=True, name="clob-worker")
        self.venue, self.warm_s, self.balance_s = venue, warm_s, balance_s
        self.on_balance, self.on_note = on_balance, on_note
        self.q: queue.Queue = queue.Queue()
        self.busy = False
        self.pings: list[float] = []
        self._last_bal = time.monotonic()

    def order(self, fn, done) -> bool:
        if self.busy:
            return False
        self.busy = True
        self.q.put((fn, done))
        return True

    def stop(self) -> None:
        self.q.put(None)

    def run(self) -> None:
        while True:
            try:
                job = self.q.get(timeout=self.warm_s)
            except queue.Empty:
                self._idle()
                continue
            if job is None:
                return
            fn, done = job
            try:
                res = fn()
            except Exception as e:  # a failed send is a result, not a dead worker
                res = {"exc": repr(e)[:300]}
            try:
                done(res)           # schedules the ack on the loop before the next order may start
            finally:
                self.busy = False

    def _idle(self) -> None:
        try:
            r = self.venue.ping()
            self.pings.append(r.ms)
            if time.monotonic() - self._last_bal >= self.balance_s and self.on_balance:
                self._last_bal = time.monotonic()
                self.on_balance(self.venue.balance())
        except Exception as e:
            if self.on_note:
                self.on_note("worker_idle_error", err=repr(e)[:200])
