"""One warm HTTP/2 session to the CLOB, every request timed on the SNTP clock.

A request records its send and response times (ns), the HTTP version, the idle time of the
connection before it (reports/infra-plan.md: +20-40 ms after >= 5 s of silence), the
Cloudflare POP and rate-limit headers. Transport errors come back as code 0, never raise."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field

import httpx

HOST = "https://clob.polymarket.com"
GEOBLOCK = "https://polymarket.com/api/geoblock"
KEEP = ("cf-ray", "retry-after", "x-ratelimit-limit", "x-ratelimit-remaining", "x-ratelimit-reset")


@dataclass
class Resp:
    method: str
    path: str
    code: int
    body: object
    t_send_ns: int
    t_ack_ns: int
    http: str = ""
    idle_s: float = float("nan")
    hdr: dict = field(default_factory=dict)
    err: str | None = None

    @property
    def ms(self) -> float:
        return (self.t_ack_ns - self.t_send_ns) / 1e6

    @property
    def ok(self) -> bool:
        return self.code == 200

    def text(self) -> str:
        return self.body if isinstance(self.body, str) else json.dumps(self.body)

    def brief(self) -> dict:
        return {"code": self.code, "ms": round(self.ms, 3), "http": self.http, "idle_s": round(self.idle_s, 3),
                "pop": self.hdr.get("cf-ray", "-").split("-")[-1], "hdr": self.hdr, "err": self.err,
                "body": self.body if len(self.text()) < 2000 else self.text()[:2000]}


class Http:
    def __init__(self, now_ns=time.time_ns, host: str = HOST, timeout: float = 5.0):
        self.now_ns, self.host = now_ns, host
        self.c = httpx.Client(http2=True, timeout=timeout,
                              headers={"User-Agent": "btclat-trade/0.1", "Accept": "*/*"})
        self.last = None   # monotonic end of the last request on this session

    def req(self, method: str, path: str, headers: dict | None = None, body: str | None = None,
            params: dict | None = None, url: str | None = None) -> Resp:
        h = dict(headers or {})
        if body is not None:
            h["Content-Type"] = "application/json"
        idle = time.monotonic() - self.last if self.last is not None else float("inf")
        t0 = self.now_ns()
        try:
            r = self.c.request(method, url or self.host + path, headers=h, params=params,
                               content=body.encode() if body is not None else None)
        except httpx.HTTPError as e:
            t1 = self.now_ns()
            self.last = time.monotonic()
            return Resp(method, path, 0, None, t0, t1, idle_s=idle, err=repr(e)[:300])
        t1 = self.now_ns()
        self.last = time.monotonic()
        try:
            b = r.json()
        except ValueError:
            b = r.text
        hdr = {k: r.headers[k] for k in KEEP if k in r.headers}
        return Resp(method, path, r.status_code, b, t0, t1, r.http_version, idle, hdr)

    def close(self) -> None:
        self.c.close()
