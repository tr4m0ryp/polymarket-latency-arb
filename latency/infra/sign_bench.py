"""Local cost of building and signing one Polymarket V2 order, nothing is sent.

A throwaway key is generated in memory (never funded, never used on the network). Times:
  lib     py-clob-client-v2 OrderBuilder.build_order (EIP-712 via eth_account), as shipped
  digest  hand-rolled EIP-712 digest with cached domain separator and type hash (keccak only)
  sign    secp256k1 sign of a ready digest (eth_keys backend: pure Python or coincurve/libsecp256k1)
  fast    digest + sign: the hot path if the order is built at trigger time
  hmac    L2 request header (HMAC-SHA256 over timestamp+method+path+body) + JSON body
Correctness: the fast path must produce the same signature as the library (RFC 6979 is
deterministic), else the benchmark is void.

    python3 latency/infra/sign_bench.py [n]     (writes data/out/infra/sign_bench.json)"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import sys
import time
from pathlib import Path

from eth_abi import encode as abi_encode
from eth_account import Account
from eth_keys import KeyAPI
from eth_utils import keccak

from py_clob_client_v2.clob_types import CreateOrderOptions, OrderArgsV2
from py_clob_client_v2.order_builder.builder import OrderBuilder
from py_clob_client_v2.order_utils.exchange_order_builder_v2 import ORDER_TYPE_HASH
from py_clob_client_v2.order_utils.model.order_data_v2 import order_to_json_v2
from py_clob_client_v2.signer import Signer

OUT = Path(__file__).resolve().parents[2] / "data/out/infra/sign_bench.json"
TOKEN = "29189400451423844915036695859305085985231594213456247445934133325687233311293"
EXCHANGE_V2 = "0xE111180000d2663C0091e4f400237545B87B996B"
ZERO32 = b"\x00" * 32


def _timeit(fn, n: int) -> dict:
    fn()  # warm caches
    ts = []
    for _ in range(n):
        t = time.perf_counter_ns()
        fn()
        ts.append(time.perf_counter_ns() - t)
    ts.sort()
    return {"p50_us": ts[n // 2] / 1e3, "p90_us": ts[int(n * 0.9)] / 1e3, "p99_us": ts[int(n * 0.99)] / 1e3}


def main(n: int = 300) -> None:
    acct = Account.create()  # throwaway, in memory only
    signer = Signer(acct.key.hex(), 137)
    ob = OrderBuilder(signer)
    opts = CreateOrderOptions(tick_size="0.01", neg_risk=False)
    args = OrderArgsV2(token_id=TOKEN, price=0.55, size=10.0, side="BUY")
    lib_order = ob.build_order(args, opts, version=2)

    dom = keccak(abi_encode(["bytes32", "bytes32", "bytes32", "uint256", "address"], [
        keccak(text="EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"),
        keccak(text="Polymarket CTF Exchange"), keccak(text="2"), 137, EXCHANGE_V2]))
    pk = KeyAPI.PrivateKey(acct.key)
    o = lib_order

    def digest(salt=int(o.salt), ts=int(o.timestamp)) -> bytes:
        sh = keccak(abi_encode(
            ["bytes32", "uint256", "address", "address", "uint256", "uint256", "uint256",
             "uint8", "uint8", "uint256", "bytes32", "bytes32"],
            [ORDER_TYPE_HASH, salt, o.maker, o.signer, int(o.tokenId), int(o.makerAmount),
             int(o.takerAmount), int(o.side), int(o.signatureType), ts, ZERO32, ZERO32]))
        return keccak(b"\x19\x01" + dom + sh)

    def fast() -> str:
        s = pk.sign_msg_hash(digest())
        return "0x" + s.to_bytes().hex()[:-2] + format(s.v + 27, "02x")

    ok = fast() == o.signature
    d = digest()
    secret = base64.urlsafe_b64encode(os.urandom(32)).decode()

    def hdr() -> str:
        body = json.dumps(order_to_json_v2(o, "throwaway-key", "FAK"), separators=(",", ":"))
        msg = str(int(time.time())) + "POST" + "/order" + body
        return base64.urlsafe_b64encode(hmac.new(base64.urlsafe_b64decode(secret),
                                                 msg.encode(), hashlib.sha256).digest()).decode()

    res = {
        "backend": type(KeyAPI().backend).__name__,
        "fast_path_matches_library_signature": ok,
        "n": n,
        "lib_build_order": _timeit(lambda: ob.build_order(args, opts, version=2), n),
        "digest_only": _timeit(digest, n),
        "sign_only": _timeit(lambda: pk.sign_msg_hash(d), n),
        "fast_digest_plus_sign": _timeit(fast, n),
        "hmac_header_plus_json": _timeit(hdr, n),
        "python": sys.version.split()[0],
    }
    print(json.dumps(res, indent=1))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tag = "coincurve" if "CoinCurve" in res["backend"] else "native"
    prev = json.loads(OUT.read_text()) if OUT.exists() else {}
    prev[tag] = res
    OUT.write_text(json.dumps(prev, indent=1))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 300)
