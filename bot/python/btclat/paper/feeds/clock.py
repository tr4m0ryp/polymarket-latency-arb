"""SNTP-corrected clock (recorder/live/clock.py) with a configurable server list: on AWS the
Amazon Time Sync Service (169.254.169.123, also chrony's source on the box), elsewhere the
recorder's public servers."""
from __future__ import annotations

from recorder.live.clock import SERVERS, Clock, sntp

AMAZON = ("169.254.169.123",)


class PaperClock(Clock):
    def __init__(self, servers=SERVERS):
        self.servers = tuple(servers)
        super().__init__()

    def sync(self) -> bool:
        best = None
        for host in self.servers:
            for _ in range(3):
                try:
                    off, rtt = sntp(host, timeout=1.0)
                except OSError:
                    continue
                if best is None or rtt < best[1]:
                    best = (off, rtt)
        if best is None:
            return False
        self.offset_ns = int(best[0] * 1e9)
        self.rtt_s = best[1]
        return True
