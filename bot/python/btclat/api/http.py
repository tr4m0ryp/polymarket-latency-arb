"""Rate-limited, retrying JSON GET with an on-disk cache for immutable data."""
from __future__ import annotations

import hashlib
import json
import random
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "cache"
GAMMA = "https://gamma-api.polymarket.com"
DATA = "https://data-api.polymarket.com"

_lock = threading.Lock()
_last_call = [0.0]
MIN_INTERVAL = 0.06  # ~16 req/s across all threads


def _throttle() -> None:
    with _lock:
        wait = _last_call[0] + MIN_INTERVAL - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last_call[0] = time.monotonic()


def _cache_path(url: str) -> Path:
    h = hashlib.sha1(url.encode()).hexdigest()
    return CACHE_DIR / h[:2] / f"{h}.json"


def get(base: str, path: str, params: dict | None = None, cache: bool = False,
        retries: int = 6):
    """GET base+path?params. With cache=True the response is stored forever:
    use it only for data that cannot change (closed markets)."""
    q = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v is not None}, doseq=True)
    url = f"{base}{path}?{q}" if q else f"{base}{path}"
    cp = _cache_path(url)
    if cache and cp.exists():
        return json.loads(cp.read_text())
    for attempt in range(retries):
        _throttle()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "btclat/0.1"})
            with urllib.request.urlopen(req, timeout=40) as r:
                data = json.loads(r.read())
            break
        except urllib.error.HTTPError as e:
            if e.code == 400:
                return []  # data-api answers 400 past its offset cap
            # 403 shows up transiently when the edge rate-limits bursts
            if e.code not in (403, 429, 500, 502, 503, 504) or attempt == retries - 1:
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == retries - 1:
                raise
        time.sleep(min(30, 1.5 ** attempt + random.random()))
    if cache:
        cp.parent.mkdir(parents=True, exist_ok=True)
        cp.write_text(json.dumps(data))
    return data
