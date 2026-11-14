"""Order signing and auth headers with the official client, py-clob-client-v2 (pinned in
deploy/requirements.txt). Imported lazily: nothing here loads until a live session starts,
so tests and the paper bot's process never import a signing library.

Measured cost (latency/infra/sign_bench.py, same library): build + EIP-712 sign 11.6 ms on
eth_keys' pure-Python backend, 1.4 ms with `coincurve` installed (deploy pins it), 0.27 ms
for a hand-rolled digest + libsecp256k1. Each order logs its own `sign_us`. A hand-rolled
signer (cached domain separator and type hash, keccak + one secp256k1 sign) would save ~1 ms
per order over coincurve: noise next to the ~113 ms arrival and the 150 ms hold, so it only
pays when pre-signing many price levels per side. Not built."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass

CHAIN_ID = 137
TICK = "0.01"


@dataclass
class Signed:
    body: str          # exact JSON sent (and HMAC-signed)
    sign_us: float     # build + EIP-712 signature
    token: str
    price: float
    size: float
    side: str
    order_type: str
    post_only: bool


class LibSigner:
    def __init__(self, creds, version: int = 2):
        from py_clob_client_v2.order_builder.builder import OrderBuilder
        from py_clob_client_v2.signer import Signer
        self._signer = Signer(creds.private_key, CHAIN_ID)
        self._builder = OrderBuilder(self._signer, signature_type=creds.sig_type, funder=creds.funder)
        self.address = self._signer.address()
        self.version = version
        try:
            from eth_keys import KeyAPI
            self.backend = type(KeyAPI().backend).__name__
        except Exception:   # informational only
            self.backend = "?"

    def order(self, token: str, price: float, size: float, side: str, order_type: str,
              post_only: bool, owner: str, expiration: int = 0) -> Signed:
        from py_clob_client_v2.clob_types import CreateOrderOptions, OrderArgsV2
        from py_clob_client_v2.order_utils.model.order_data_v2 import order_to_json_v2
        t0 = time.perf_counter_ns()
        o = self._builder.build_order(OrderArgsV2(token_id=token, price=price, size=size, side=side,
                                                  expiration=expiration),
                                      CreateOrderOptions(tick_size=TICK, neg_risk=False), version=self.version)
        us = (time.perf_counter_ns() - t0) / 1e3
        payload = order_to_json_v2(o, owner, order_type, post_only, False)
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        return Signed(body, us, token, price, size, side, order_type, post_only)

    def l1_headers(self, ts: int, nonce: int = 0) -> dict:
        from py_clob_client_v2.headers.headers import create_level_1_headers
        return create_level_1_headers(self._signer, nonce=nonce, timestamp=ts)

    def l2_headers(self, api: dict, method: str, path: str, body: str | None, ts: int) -> dict:
        from py_clob_client_v2.clob_types import ApiCreds, RequestArgs
        from py_clob_client_v2.headers.headers import create_level_2_headers
        creds = ApiCreds(api["key"], api["secret"], api["passphrase"])
        ra = RequestArgs(method=method, request_path=path, body=None, serialized_body=body)
        return create_level_2_headers(self._signer, creds, ra, timestamp=ts)
