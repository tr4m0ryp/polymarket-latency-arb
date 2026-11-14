"""Hard rule: the paper bot has no order-sending path.

It never imports a signing library or an order client: `install()` blocks those imports
for the whole process (raises ImportError) and refuses to start if one is already loaded.
Network use is read-only by construction: public websockets (Binance, Polymarket market
channel) and HTTP GET to Gamma. tests/paper/test_guard.py also scans this package's source
for order endpoints and signing calls."""
from __future__ import annotations

import importlib.abc
import sys

FORBIDDEN = ("py_clob_client", "py_clob_client_v2", "clob_client", "eth_account", "eth_keys",
             "eth_utils", "web3", "coincurve", "secp256k1", "ecdsa", "nacl", "eip712",
             "poly_eip712_structs", "py_order_utils", "boto3", "botocore")


class OrderPathBlocked(ImportError):
    pass


class _Block(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] in FORBIDDEN:
            raise OrderPathBlocked(f"paper bot: import of {name!r} is forbidden (no order path)")
        return None


def loaded() -> list[str]:
    return sorted({m.split(".")[0] for m in sys.modules} & set(FORBIDDEN))


def install() -> None:
    bad = loaded()
    if bad:
        raise SystemExit(f"paper bot: forbidden modules already imported: {bad}")
    if not any(isinstance(f, _Block) for f in sys.meta_path):
        sys.meta_path.insert(0, _Block())
