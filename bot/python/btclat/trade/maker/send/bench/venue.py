"""The client side of the benchmark: the real signer (py-clob-client-v2) on a throwaway key that
never touches a network, else an emulated signer of the same CPU cost; L2-style HMAC headers;
a Hedge of k sessions to the local server. Built the same way in the parent (thread sender)
and in the sender process (spec factory "...bench.venue:bench_venue")."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time

from ....venue.http import Http
from ....venue.signer import Signed
from ...ops.hedge import Hedge


class _Emulated:
    backend = "emulated"

    def __init__(self, us: float = 1400.0):
        self.n = 20000
        best = min(self._timed() for _ in range(5))
        self.n = max(1, int(self.n * us / 1e6 / max(best, 1e-9)))

    def _timed(self) -> float:
        t0 = time.perf_counter()
        self._burn()
        return time.perf_counter() - t0

    def _burn(self) -> int:
        x = 0
        for i in range(self.n):
            x = (x * 31 + i) & 0xFFFFFFFF
        return x

    def order(self, token, price, size, side, order_type, post_only, owner, expiration=0) -> Signed:
        t0 = time.perf_counter_ns()
        self._burn()
        body = json.dumps({"order": {"tokenId": token, "price": price, "size": size, "side": side,
                                     "expiration": expiration, "salt": os.urandom(8).hex()},
                           "owner": owner, "orderType": order_type, "postOnly": post_only})
        return Signed(body, (time.perf_counter_ns() - t0) / 1e3, token, price, size, side, order_type, post_only)


def signer(kind: str):
    if kind == "real":
        try:
            from ....gate.creds import Creds
            from ....venue.signer import LibSigner
            return LibSigner(Creds("0x" + os.urandom(32).hex(), "0x" + "00" * 20, 0))
        except Exception:  # library missing: emulate its cost
            pass
    return _Emulated()


class BenchVenue:
    SECRET = base64.urlsafe_b64encode(b"bench-secret-not-a-key").decode()

    def __init__(self, kind: str = "real"):
        self.signer = signer(kind)

    def sign(self, token, price, size, side="BUY", order_type="GTD", post_only=False, expiration=0) -> Signed:
        return self.signer.order(token, price, size, side, order_type, post_only, "bench", expiration)

    def _l2(self, method: str, path: str, body: str | None) -> dict:
        ts = str(int(time.time()))
        msg = ts + method + path + (body or "")
        sig = base64.urlsafe_b64encode(hmac.new(base64.urlsafe_b64decode(self.SECRET), msg.encode(),
                                                hashlib.sha256).digest()).decode()
        return {"POLY_ADDRESS": "0x" + "00" * 20, "POLY_SIGNATURE": sig, "POLY_TIMESTAMP": ts,
                "POLY_API_KEY": "bench", "POLY_PASSPHRASE": "bench"}

    def post_headers(self, signed) -> dict:
        return self._l2("POST", "/order", signed.body)

    def cancel_req(self, oid: str) -> tuple[str, dict]:
        body = json.dumps({"orderID": oid}, separators=(",", ":"))
        return body, self._l2("DELETE", "/order", body)


def bench_venue(spec: dict, now_ns):
    host = spec["host"]
    return BenchVenue(spec.get("sign", "real")), Hedge(now_ns, spec["k"], sessions=[
        Http(now_ns, host=host) for _ in range(spec["k"])])
