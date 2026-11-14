"""The recorded 5m markets, their resolved outcome, and the recorder's feed gaps.

Outcome: Gamma `outcomePrices` of the closed market (cached as JSON under
data/cache/strategy/outcomes.json); fallback = the Up book mid in the last seconds."""
from __future__ import annotations

import gzip
import json
import sys
import time
import urllib.request
import zlib

import pandas as pd

from .. import CACHE, LIVE, ROOT

sys.path.insert(0, str(ROOT))


def _rows(stream: str):
    for p in sorted(LIVE.glob(f"*/{stream}-*.tsv.gz")):
        try:
            with gzip.open(p, "rt") as fh:
                for line in fh:
                    t, _, raw = line.rstrip("\n").partition("\t")
                    if raw:
                        yield int(t) / 1e9, json.loads(raw)
        except (EOFError, zlib.error, gzip.BadGzipFile):
            continue


def markets(fam: str = "5m") -> pd.DataFrame:
    """One row per recorded market, indexed 0..n-1 in start order (stable across runs
    as long as no older market is added)."""
    df = pd.DataFrame([j for _, j in _rows("markets")]).drop_duplicates("slug")
    df = df[df["fam"] == fam].sort_values("start").reset_index(drop=True)
    return df


def assets(mk: pd.DataFrame) -> dict[str, tuple[int, bool]]:
    out = {}
    for i, m in enumerate(mk.itertuples()):
        out[m.up] = (i, True)
        out[m.down] = (i, False)
    return out


def _gamma_outcome(slug: str) -> float | None:
    req = urllib.request.Request(f"https://gamma-api.polymarket.com/markets?slug={slug}&closed=true",
                                 headers={"User-Agent": "btclat/0.1"})
    with urllib.request.urlopen(req, timeout=15) as r:
        rows = json.loads(r.read())
    if not rows:
        return None
    m = rows[0]
    try:
        outs, px = json.loads(m["outcomes"]), [float(x) for x in json.loads(m["outcomePrices"])]
    except (KeyError, TypeError, ValueError):
        return None
    if max(px) < 0.99:
        return None
    return float(px[outs.index("Up")] > 0.5)


def outcomes(mk: pd.DataFrame) -> dict[str, float]:
    """slug -> 1.0 if Up won, 0.0 if Down won (closed markets only)."""
    p = CACHE / "outcomes.json"
    have = json.loads(p.read_text()) if p.exists() else {}
    now = time.time()
    for m in mk.itertuples():
        if m.slug in have or m.end > now - 120:
            continue
        try:
            o = _gamma_outcome(m.slug)
        except OSError:
            o = None
        if o is not None:
            have[m.slug] = o
        time.sleep(0.07)
    CACHE.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(have))
    return have


def gaps(pad_before: float = 30.0, pad_after: float = 5.0) -> dict[str, list[tuple[float, float]]]:
    """slug -> [(t0, t1)] windows to exclude: from `pad_before` s before a socket error
    (backlog builds up before the server closes a slow consumer) to `pad_after` s after
    the reconnect."""
    out, open_err = {}, {}
    for t, j in _rows("events"):
        feed = j.get("feed", "")
        if not feed.startswith("clob:"):
            continue
        slug = feed[5:]
        if j["kind"] == "error":
            open_err.setdefault(slug, t)
        elif j["kind"] == "connect" and slug in open_err:
            out.setdefault(slug, []).append((open_err.pop(slug) - pad_before, t + pad_after))
    return out
