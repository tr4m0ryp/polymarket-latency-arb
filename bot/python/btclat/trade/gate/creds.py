"""Credentials file `~/.config/btclat/polymarket.env`: KEY=VALUE lines, `#` comments.

    POLY_PRIVATE_KEY=0x<64 hex>     signer key (EOA that controls the Polymarket wallet)
    POLY_FUNDER=0x<40 hex>          wallet that holds the pUSD (profile menu on polymarket.com;
                                    the signer's own address for an EOA account)
    POLY_SIGNATURE_TYPE=3           0 EOA, 1 POLY_PROXY, 2 GNOSIS_SAFE, 3 POLY_1271 (deposit wallet)
    POLY_API_KEY=...                optional L2 creds (all three or none; derived when absent)
    POLY_API_SECRET=...
    POLY_API_PASSPHRASE=...

The file must be owned by the user running the bot and unreadable by anyone else (mode 600
or 400), in a directory nobody else can write. Values are never printed (`Creds.__repr__`)."""
from __future__ import annotations

import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path

HEX_KEY = re.compile(r"^0x[0-9a-fA-F]{64}$")
HEX_ADDR = re.compile(r"^0x[0-9a-fA-F]{40}$")
API = ("POLY_API_KEY", "POLY_API_SECRET", "POLY_API_PASSPHRASE")


class CredsError(SystemExit):
    pass


@dataclass(frozen=True)
class Creds:
    private_key: str
    funder: str
    sig_type: int
    api_key: str | None = None
    api_secret: str | None = None
    api_passphrase: str | None = None

    def __repr__(self) -> str:
        return f"Creds(funder={self.funder}, sig_type={self.sig_type}, l2={'set' if self.api_key else 'derive'})"

    __str__ = __repr__

    @property
    def has_l2(self) -> bool:
        return bool(self.api_key)


def check_perms(path: Path) -> None:
    try:
        st = path.stat()
    except FileNotFoundError:
        raise CredsError(f"no credentials file {path}; see btclat/trade/gate/creds.py for the format")
    if not stat.S_ISREG(st.st_mode):
        raise CredsError(f"{path} is not a regular file")
    if st.st_uid != os.getuid():
        raise CredsError(f"{path} is owned by uid {st.st_uid}, not by this user ({os.getuid()})")
    if st.st_mode & 0o077:
        raise CredsError(f"{path} has mode {oct(st.st_mode & 0o777)}; run: chmod 600 {path}")
    d = path.parent.stat()
    if d.st_mode & 0o022:
        raise CredsError(f"{path.parent} is writable by group/others; run: chmod 700 {path.parent}")


def parse(text: str) -> dict[str, str]:
    out = {}
    for n, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        k, sep, v = line.partition("=")
        if not sep:
            raise CredsError(f"credentials line {n}: expected KEY=VALUE")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def load(path: Path) -> Creds:
    check_perms(path)
    d = parse(path.read_text())
    pk, funder, st = d.get("POLY_PRIVATE_KEY", ""), d.get("POLY_FUNDER", ""), d.get("POLY_SIGNATURE_TYPE", "")
    if not pk.startswith("0x"):
        pk = "0x" + pk
    if not HEX_KEY.match(pk):
        raise CredsError("POLY_PRIVATE_KEY must be 32 bytes hex")
    if not HEX_ADDR.match(funder):
        raise CredsError("POLY_FUNDER must be a 0x address (40 hex)")
    if st not in ("0", "1", "2", "3"):
        raise CredsError("POLY_SIGNATURE_TYPE must be 0, 1, 2 or 3")
    api = [d.get(k) or None for k in API]
    if any(api) and not all(api):
        raise CredsError(f"set all of {API} or none (then they are derived)")
    return Creds(pk, funder, int(st), *api)
