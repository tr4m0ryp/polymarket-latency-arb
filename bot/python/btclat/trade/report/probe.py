"""Probe-run sections: signing cost, POST ack and cancel round trips split warm / idle,
error kinds and HTTP codes, cancel confirmation, Cloudflare POP and rate-limit headers."""
from __future__ import annotations

import pandas as pd

from research.predict.report.md import md

from .stats import pct


def _get(df: pd.DataFrame, col: str, key: str) -> pd.Series:
    return df[col].map(lambda d: d.get(key) if isinstance(d, dict) else None) if col in df else pd.Series(dtype=float)


def section(df: pd.DataFrame) -> list[str]:
    if not len(df):
        return ["(no probe cycles)"]
    s = df[df["decision"] == "sent"].copy()
    lat = []
    for warm, g in s.groupby("warm"):
        tag = "warm" if warm else "idle"
        lat.append({"what": f"POST ack ({tag})", **pct(_get(g, "post", "ms"))})
        lat.append({"what": f"cancel ({tag})", **pct(_get(g, "cancel", "ms"))})
        lat.append({"what": f"idle before POST s ({tag})", **pct(_get(g, "post", "idle_s"))})
    lat.append({"what": "sign (ms)", **pct(s.get("sign_us", pd.Series(dtype=float)), 1e-3)})
    lat.append({"what": "book GET (data session)", **pct(df.get("book_ms", pd.Series(dtype=float)))})
    pings = [x for v in df.get("ping_ms", pd.Series(dtype=object)).dropna() for x in v]
    lat.append({"what": "keep-warm GET /time", **pct(pings)})
    codes = _get(s, "post", "code").value_counts()
    kinds = s["err_kind"].fillna("ok").value_counts() if "err_kind" in s else pd.Series(dtype=int)
    pops = _get(s, "post", "pop").value_counts()
    http = _get(s, "post", "http").value_counts()
    rl = [h for h in _get(s, "post", "hdr").dropna() if any(k.startswith("x-ratelimit") or k == "retry-after" for k in h)]
    canc = s["cancelled"].fillna(False).astype(bool) if "cancelled" in s else pd.Series(dtype=bool)
    return [f"cycles {len(df)}, sent {len(s)}, cancel confirmed {int(canc.sum())} of {int(s['order_id'].notna().sum()) if 'order_id' in s else 0}",
            "Skipped: " + (", ".join(f"{k} {v}" for k, v in df.loc[df['decision'] != 'sent', 'decision'].value_counts().items()) or "none"),
            "POST HTTP codes: " + ", ".join(f"{k} {v}" for k, v in codes.items()),
            "Result kinds: " + ", ".join(f"{k} {v}" for k, v in kinds.items()),
            "Cloudflare POP: " + ", ".join(f"{k} {v}" for k, v in pops.items()) + "; HTTP: " + ", ".join(f"{k} {v}" for k, v in http.items()),
            f"Rate-limit headers seen on {len(rl)} responses" + (f", last {rl[-1]}" if rl else ""), "",
            "Round trips (ms):", "", md(pd.DataFrame(lat), 2)]
