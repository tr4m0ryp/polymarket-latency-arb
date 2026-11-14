"""What must hold before the live test may touch the venue. Offline part (no network):
`--i-approve` given, no kill file, today's UTC day not locked by the loss cap, credentials
file present with safe permissions. Online part (the venue client, mocked in tests): not
geoblocked (IE and JP are API-allowed; GB, US, FR, DE ... are close-only on the API), CLOB
on the exchange version this code signs for (2), enough pUSD and a non-zero allowance."""
from __future__ import annotations

import os
import time
from pathlib import Path

from ..risk.book import lock_path, utc_day
from . import creds as cr

CONFIG = Path(os.environ.get("BTCLAT_CONFIG", "~/.config/btclat")).expanduser()
MIN_BALANCE = {"probe": 0.25, "probe0": 0.0, "micro": 5.0, "holdtest": 5.0, "holddup": 0.25, "maker": 5.0}     # $ pUSD at start
# polymarket.com/api/geoblock reports the frontend flag: these are close-only on the website
# but API-unrestricted (docs.polymarket.com/api-reference/geoblock), so blocked=true is fine here.
API_ALLOWED = frozenset({"IE", "JP", "NL", "KR"})
EXCHANGE_VERSION = 2


class Refused(SystemExit):
    pass


def paths(config: Path = CONFIG) -> dict[str, Path]:
    return {"creds": config / "polymarket.env", "kill": config / "KILL", "state": config / "state"}


def offline(approve: bool, config: Path = CONFIG, now: float | None = None) -> cr.Creds:
    p = paths(config)
    if not approve:
        raise Refused("refusing: live orders need --i-approve (and the user's explicit approval)")
    if p["kill"].exists():
        raise Refused(f"refusing: kill file {p['kill']} exists (remove it to allow a start)")
    day = utc_day(time.time() if now is None else now)
    if lock_path(p["state"], day).exists():
        raise Refused(f"refusing: UTC day {day} is locked by the loss cap ({lock_path(p['state'], day)})")
    try:
        return cr.load(p["creds"])
    except cr.CredsError as e:
        raise Refused(f"refusing: {e}") from None


def online(venue, mode: str) -> dict:
    g = venue.geoblock()
    ok = isinstance(g, dict) and (g.get("blocked") is False or
                                  (g.get("blocked") is True and g.get("country") in API_ALLOWED))
    if not ok:
        raise Refused(f"refusing: geoblock says {g!r} (orders from this IP are rejected or close-only)")
    v = venue.version()
    if v != EXCHANGE_VERSION:
        raise Refused(f"refusing: CLOB exchange version {v}, this code signs version {EXCHANGE_VERSION}")
    bal = venue.balance()
    if bal["balance"] < MIN_BALANCE[mode]:
        raise Refused(f"refusing: pUSD balance ${bal['balance']:.2f} < ${MIN_BALANCE[mode]} for {mode} "
                      f"(HTTP {bal.get('code')})")
    if not bal["allowance_ok"]:
        raise Refused("refusing: pUSD allowance to the exchange is zero (run the trading approvals)")
    return {"geoblock": g, "version": v, **bal}
