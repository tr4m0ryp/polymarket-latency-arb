"""The live CLOB client the probe and micro modes talk to: one warm HTTP/2 session (http.py)
plus the official signer (signer.py). Tests replace this whole object with a fake of the
same methods. Every call returns parsed data plus the timed `Resp`.

Auth headers carry the CLOB server's clock (offset from GET /time at connect): a host clock
16 s off was seen on the recorder box, and L2 headers are timestamped."""
from __future__ import annotations

import json
import time

from . import parse
from .http import GEOBLOCK, Http
from .signer import LibSigner

BALANCE = "/balance-allowance"
TRADES = "/data/trades"


class LiveClob:
    def __init__(self, creds, now_ns=time.time_ns, http: Http | None = None, signer=None):
        self.creds = creds
        self.http = http or Http(now_ns)          # orders, cancels, auth: the timed session
        self.data = Http(now_ns) if http is None else http   # public book reads, kept off it
        self.signer = signer or LibSigner(creds)
        self.api = ({"key": creds.api_key, "secret": creds.api_secret, "passphrase": creds.api_passphrase}
                    if creds.has_l2 else None)
        self.offset_s = 0.0
        self.derived = False

    # public ------------------------------------------------------------------------------
    def ping(self):
        return self.http.req("GET", "/time")

    def geoblock(self) -> dict:
        r = self.http.req("GET", "", url=GEOBLOCK)
        return r.body if isinstance(r.body, dict) else {"blocked": None, "code": r.code, "err": r.err}

    def version(self) -> int:
        r = self.http.req("GET", "/version")
        return int(r.body.get("version", -1)) if isinstance(r.body, dict) else -1

    def book(self, token: str) -> dict:
        r = self.data.req("GET", "/book", params={"token_id": token})
        bb, ba = parse.best(r)
        return {"bb": bb, "ba": ba, "resp": r}

    # auth --------------------------------------------------------------------------------
    def _ts(self) -> int:
        return int(time.time() + self.offset_s)

    def connect(self) -> None:
        """Server clock offset, then L2 creds (derived from the key when the file has none)."""
        t0 = time.time()
        r = self.ping()
        t1 = time.time()
        if r.ok:
            self.offset_s = float(r.body if not isinstance(r.body, dict) else r.body.get("time", t1)) - (t0 + t1) / 2
        if self.api is None:
            h = self.signer.l1_headers(self._ts())
            r = self.http.req("GET", "/auth/derive-api-key", headers=h)
            if not r.ok:
                r = self.http.req("POST", "/auth/api-key", headers=self.signer.l1_headers(self._ts()))
            if not r.ok or not isinstance(r.body, dict):
                raise SystemExit(f"refusing: could not derive L2 API creds (HTTP {r.code}: {r.text()[:200]})")
            self.api = {"key": r.body["apiKey"], "secret": r.body["secret"], "passphrase": r.body["passphrase"]}
            self.derived = True

    def _l2(self, method: str, path: str, body: str | None = None) -> dict:
        return self.signer.l2_headers(self.api, method, path, body, self._ts())

    # private -----------------------------------------------------------------------------
    def balance(self) -> dict:
        r = self.http.req("GET", BALANCE, headers=self._l2("GET", BALANCE),
                          params={"asset_type": "COLLATERAL", "signature_type": self.creds.sig_type})
        return parse.balance(r)

    def sign(self, token: str, price: float, size: float, side: str = "BUY", order_type: str = "FAK",
             post_only: bool = False, expiration: int = 0):
        """`expiration` (unix s, server clock) only for GTD; the venue wants it >= now + 60 s."""
        return self.signer.order(token, price, size, side, order_type, post_only, self.api["key"], expiration)

    def server_now(self) -> float:
        return time.time() + self.offset_s

    def post_headers(self, signed) -> dict:
        """L2 headers of a POST /order, reusable for identical copies (venue/fanout.py)."""
        return self._l2("POST", "/order", signed.body)

    def post(self, signed):
        return self.http.req("POST", "/order", headers=self.post_headers(signed), body=signed.body)

    def get_order(self, oid: str):
        path = f"/data/order/{oid}"
        return self.http.req("GET", path, headers=self._l2("GET", path))

    def trades(self, after: int, pages: int = 10) -> list[dict]:
        """Our trades (maker or taker) matched since `after` (unix s): GET /data/trades, L2-signed
        on the bare path as the official client does, cursor-paginated. No address filter: the
        L2 key scopes it to our account (a wrong maker_address would silently answer []).
        Raises on an error answer so a caller never mistakes a failed read for "no trades"."""
        out, cursor = [], "MA=="
        for _ in range(pages):
            r = self.http.req("GET", TRADES, headers=self._l2("GET", TRADES),
                              params={"after": int(after), "next_cursor": cursor})
            if r.code != 200 or not isinstance(r.body, (dict, list)):
                raise RuntimeError(f"GET {TRADES}: HTTP {r.code} {r.text()[:200]}")
            if isinstance(r.body, list):
                return out + r.body
            out += r.body.get("data") or []
            cursor = r.body.get("next_cursor")
            if not cursor or cursor == "LTE=":
                break
        return out

    def cancel_req(self, oid: str) -> tuple[str, dict]:
        """Body and L2 headers of DELETE /order, reusable for identical copies (maker/ops)."""
        body = json.dumps({"orderID": oid}, separators=(",", ":"))
        return body, self._l2("DELETE", "/order", body)

    def cancel(self, oid: str):
        body, headers = self.cancel_req(oid)
        return self.http.req("DELETE", "/order", headers=headers, body=body)

    def cancel_all(self):
        return self.http.req("DELETE", "/cancel-all", headers=self._l2("DELETE", "/cancel-all"))

    def info(self) -> dict:
        return {"address": self.signer.address, "funder": self.creds.funder, "sig_type": self.creds.sig_type,
                "sign_backend": getattr(self.signer, "backend", "?"), "l2_derived": self.derived,
                "server_offset_s": round(self.offset_s, 3)}

    def close(self) -> None:
        self.http.close()
        if self.data is not self.http:
            self.data.close()
