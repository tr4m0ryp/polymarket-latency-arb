"""A maker run's order operations with every timestamp we log, one row per insert / cancel.

Columns (ms unless named): dec_log = decision -> ops line written (manager + risk gate), log_send =
ops line -> first copy's t_send (pool hand-off + signing for inserts), sign = signing alone,
skew = last copy's send - first copy's send (are the k copies really parallel?), rtt = first good
copy's round trip, rtt_min = fastest copy, ack_spread = last copy's ack - first copy's ack."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from recorder.live.sink import read_stream


def _rows(root: Path, name: str) -> list[tuple[int, dict]]:
    out = []
    for d in (root, root / "raw"):
        out += [(t, json.loads(raw)) for t, raw in read_stream(name, root=d)]
    return sorted(out, key=lambda x: x[0])


def frame(root: Path) -> pd.DataFrame:
    ops = _rows(root, "ops")
    cps = {(r["what"], r["cid"]): r["copies"] for _, r in _rows(root, "events") if r.get("kind") == "copies"}
    sent: dict = {}
    out = []
    for t, r in ops:
        k, cid = r["kind"], r["cid"]
        if k in ("insert", "cancel"):
            sent[(k, cid)] = (t, r)
            continue
        if k not in ("insert_ack", "cancel_ack") or "t_send_ns" not in r:
            continue
        what = k[:-4]
        t_log, req = sent.get((what, cid), (None, {}))
        cp = cps.get((what, cid), [])
        sends = [c["t_send_ns"] for c in cp] or [r["t_send_ns"]]
        acks = [c["t_ack_ns"] for c in cp if c.get("code")] or [r["t_ack_ns"]]
        out.append({
            "what": what, "cid": cid, "slug": r["slug"], "token": r["token"], "price": r["price"],
            "side": r["side"], "oid": r.get("oid") or r.get("order_id"), "ok": bool(r.get("ok") or r.get("confirmed")),
            "k": r.get("k"), "via": r.get("via", "thread"), "t_dec": r.get("t_dec"), "t_log_ns": t_log, "t_send_ns": r["t_send_ns"],
            "t_ack_ns": r["t_ack_ns"], "rtt": r["ms"], "sign": (r.get("sign_us") or float("nan")) / 1e3,
            "dec_log": (t_log / 1e9 - r["t_dec"]) * 1e3 if t_log and what == "insert" else float("nan"),
            "log_send": (min(sends) - t_log) / 1e6 if t_log else float("nan"),
            "skew": (max(sends) - min(sends)) / 1e6,
            "rtt_min": min(c["ms"] for c in cp) if cp else r["ms"],
            "ack_spread": (max(acks) - min(acks)) / 1e6,
            "pop": ",".join(sorted({c.get("pop", "-") for c in cp})),
        })
    return pd.DataFrame(out)


def lookups(root: Path) -> pd.Series:
    return pd.Series([r["ms"] for _, r in _rows(root, "ops") if r["kind"] == "lookup" and "ms" in r], dtype=float)


def warm(root: Path) -> pd.Series:
    """The keep-warm GET /time round trips the stats lines carry (one per minute, k values)."""
    return pd.Series([x for _, r in _rows(root, "events") if r.get("kind") == "stats"
                      for x in (r.get("warm_ms") or [])], dtype=float)
