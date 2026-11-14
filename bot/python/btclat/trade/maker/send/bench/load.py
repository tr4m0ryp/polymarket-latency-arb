"""Feed-like load on the event loop: `rate` messages/s, each a json.loads of a CLOB-sized
price_change plus `us` microseconds of Python work (the paper bot's book update, features and
decision), in 2 ms batches. The live bot: ~3,400 msgs/s around its sends, 21 CPU-min / 60 min."""
from __future__ import annotations

import asyncio
import json
import time

MSG = json.dumps({"market": "0x" + "ab" * 32, "event_type": "price_change", "timestamp": "1791986957478",
                  "price_changes": [{"asset_id": str(10 ** 76 + i), "price": "0.33", "size": "878.5", "side": "BUY",
                                     "hash": "f" * 40, "best_bid": "0.25", "best_ask": "0.28"} for i in range(2)]})


class Load:
    def __init__(self, rate: float, us: float):
        self.rate, self.us, self.n = rate, us, 0
        self.book: dict = {}
        self.k = self._calibrate()

    def _work(self, k: int) -> None:
        j = json.loads(MSG)
        for c in j["price_changes"]:
            self.book[(c["asset_id"], c["price"])] = float(c["size"])
        x = 0
        for i in range(k):
            x = (x * 31 + i) & 0xFFFFFFFF

    def _calibrate(self) -> int:
        t0 = time.perf_counter()
        for _ in range(200):
            self._work(0)
        base = (time.perf_counter() - t0) / 200
        t0 = time.perf_counter()
        self._work(20000)
        per = max((time.perf_counter() - t0 - base) / 20000, 1e-9)
        return max(0, int((self.us / 1e6 - base) / per))

    async def run(self, stop: asyncio.Event) -> None:
        if self.rate <= 0:
            await stop.wait()
            return
        t_next, owed = time.perf_counter(), 0.0
        while not stop.is_set():
            now = time.perf_counter()
            owed += (now - t_next) * self.rate if now > t_next else 0.0
            t_next = now
            while owed >= 1:
                self._work(self.k)
                self.n += 1
                owed -= 1
            await asyncio.sleep(0.002)
