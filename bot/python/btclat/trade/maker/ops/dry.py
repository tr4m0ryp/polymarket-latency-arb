"""Dry operations: nothing leaves the process. An insert or cancel takes effect at the venue
`L` s after the decision (the simulator's L row, 50 ms by default) and is acked then; a
post-only insert that would cross our book view at that instant is rejected, as the
simulator's maker rejects it (research/strategy/sim/maker.py). Fills come from fills/infer.py.

NullVenue stands in for the client in the session shell: cancel-all is a logged no-op."""
from __future__ import annotations

from types import SimpleNamespace


def crosses(book, side: str, tick: int) -> bool:
    """Would a post-only quote at this Up-frame tick take liquidity on our Up book view?"""
    if book is None:
        return False
    return book.ba <= tick if side == "bid" else book.bb >= tick


class DryOps:
    def __init__(self, later, now, book_of, L: float = 0.050):
        self.later, self.now, self.book_of, self.L = later, now, book_of, L

    def server_now(self) -> float:
        return self.now()

    def _stamp(self, t0: float) -> dict:
        t = self.now()
        return {"t_send_ns": int(t0 * 1e9), "t_ack_ns": int(t * 1e9), "ms": round((t - t0) * 1e3, 3),
                "t_venue": t, "k": 0, "dry": True}

    def insert(self, o, cb) -> None:
        t0 = self.now()

        def ack():
            if crosses(self.book_of(o.slug), o.side, o.tick):
                cb({"ok": False, "status": "rejected", "order_id": None, "fill_sh": 0.0,
                    "err_kind": "post_only_crosses", "err": "dry: post-only quote crosses the book", **self._stamp(t0)})
            else:
                cb({"ok": True, "status": "live", "order_id": f"dry:{o.cid}", "fill_sh": 0.0, "err_kind": None,
                    **self._stamp(t0)})
        self.later(self.L, ack)

    def cancel(self, o, cb) -> None:
        t0 = self.now()
        self.later(self.L, lambda: cb({"confirmed": True, **self._stamp(t0)}))

    def lookup(self, o, cb) -> None:
        cb({"status": "canceled" if o.state == "done" else "live", "fill_sh": o.matched, "unknown": False,
            "t_ack": self.now()})

    def balance(self) -> dict:
        return {"balance": None}

    def keep_warm(self) -> list[float]:
        return []

    def close(self) -> None:
        pass


class NullVenue:
    def cancel_all(self):
        return SimpleNamespace(ok=True, brief=lambda: {"dry": True})

    def info(self) -> dict:
        return {"dry": True}

    def close(self) -> None:
        pass
