"""Wall clock corrected by SNTP. The host's chrony has no servers configured
(it ran 8.3 s slow on 2026-10-09), so the recorder measures its own offset and
stamps every message with local time + offset. Offsets are logged so analysis
can audit or re-apply them."""
from __future__ import annotations

import socket
import struct
import time

SERVERS = ("time.cloudflare.com", "time.google.com", "pool.ntp.org")
NTP_EPOCH = 2208988800


def sntp(host: str, timeout: float = 2.0) -> tuple[float, float]:
    """One SNTP exchange: (offset_s, rtt_s), offset = server - local."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    try:
        t0 = time.time()
        s.sendto(b"\x1b" + 47 * b"\0", (host, 123))
        d, _ = s.recvfrom(48)
        t3 = time.time()
    finally:
        s.close()
    rx_s, rx_f, tx_s, tx_f = struct.unpack("!IIII", d[32:48])
    t1 = rx_s - NTP_EPOCH + rx_f / 2**32
    t2 = tx_s - NTP_EPOCH + tx_f / 2**32
    return ((t1 - t0) + (t2 - t3)) / 2, (t3 - t0) - (t2 - t1)


class Clock:
    def __init__(self) -> None:
        self.offset_ns = 0
        self.rtt_s = float("nan")
        self.sync()

    def sync(self) -> bool:
        """Keep the lowest-RTT sample of a few servers; False if all fail."""
        best = None
        for host in SERVERS:
            for _ in range(3):
                try:
                    off, rtt = sntp(host)
                except OSError:
                    continue
                if best is None or rtt < best[1]:
                    best = (off, rtt)
        if best is None:
            return False
        self.offset_ns = int(best[0] * 1e9)
        self.rtt_s = best[1]
        return True

    def now_ns(self) -> int:
        return time.time_ns() + self.offset_ns

    def now(self) -> float:
        return self.now_ns() / 1e9
