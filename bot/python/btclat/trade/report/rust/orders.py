"""One row per order, joined from the event streams (signal, order, send, ack, fill, book, settle),
in the column vocabulary of the micro report (btclat/trade/report/micro.py).

Times: t_signal / t_decision / t_event_venue are wall seconds, t_send_ns / t_ack_ns wall ns (the
first copy sent, the earliest ack received); *_mono_ns are CLOCK_MONOTONIC and give the exact
latencies. Prices are in the bought token's terms. Fees default to 0.07 p (1 - p) per share (our
0% maker-rebate tier, taker side) when the fill event carries none. Paper columns are NaN."""
from __future__ import annotations

import math
from collections import defaultdict

import numpy as np
import pandas as pd

from .load import get

FEE = 0.07
AT = {"signal": "sig", "send": "send", "ack": "ack", "ack+3s": "a3", "ack+10s": "a10"}


def num(x) -> float:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return math.nan
    return v


def nn(x):
    """None for NaN / None (a frame round trip turns missing values into NaN)."""
    return None if x is None or (isinstance(x, float) and x != x) else x


def fee_of(px: float, sh: float) -> float:
    return FEE * px * (1 - px) * sh


def _by(df: pd.DataFrame, key: str) -> dict[str, list[dict]]:
    out = defaultdict(list)
    for r in df.to_dict("records") if len(df) else []:
        out[r.get(key)].append(r)
    return out


def _fills(evs: list[dict], acks: list[dict]) -> dict:
    """Deduplicate fill events by trade_id (any src); fall back to the ack's fill_sh / fill_cost."""
    seen, sh, cost, fee, src = set(), 0.0, 0.0, 0.0, None
    for f in evs:
        s, px = num(f.get("sh")), num(f.get("px"))
        if not s > 0:
            continue
        key = f.get("trade_id") or (f.get("order_id"), s, px, f.get("match_t"))
        if key in seen:
            continue
        seen.add(key)
        c = num(f.get("cost"))
        c = c if c == c else s * px
        fe = num(f.get("fee"))
        sh, cost, fee, src = sh + s, cost + c, fee + (fe if fe == fe else fee_of(c / s, s)), src or f.get("src")
    if sh == 0:
        best = max(acks, key=lambda a: num(a.get("fill_sh")) if num(a.get("fill_sh")) == num(a.get("fill_sh")) else 0, default=None)
        s = num(best.get("fill_sh")) if best else math.nan
        if s > 0:
            c = num(best.get("fill_cost"))
            c = c if c == c else s * num(best.get("px"))
            sh, cost, fee, src = s, c, fee_of(c / s, s), "ack"
    return {"fill_sh": sh, "fill_cost": cost, "fee": fee, "px": cost / sh if sh > 0 else math.nan, "fill_src": src}


def _timing(sends: list[dict], acks: list[dict]) -> dict:
    out = {"sent": bool(sends), "n_copies": len(sends), "t_send_ns": math.nan, "t_send_mono_ns": math.nan,
           "t_ack_ns": math.nan, "t_ack_mono_ns": math.nan, "first_ack_ms": math.nan, "copy_lat_ms": [],
           "err_kind": None, "ack_ok": None, "status": None, "order_id": None, "code": math.nan}
    if sends:
        out["t_send_ns"] = min(num(s.get("t_send_wall_ns")) for s in sends)
        out["t_send_mono_ns"] = min(num(s.get("t_send_mono_ns")) for s in sends)
    if acks:
        real = [a for a in acks if num(a.get("code")) > 0] or acks   # code 0 = transport error
        first = min(real, key=lambda a: num(a.get("t_ack_mono_ns")))
        out["t_ack_ns"], out["t_ack_mono_ns"] = num(first.get("t_ack_wall_ns")), num(first.get("t_ack_mono_ns"))
        out["first_ack_ms"] = (out["t_ack_mono_ns"] - out["t_send_mono_ns"]) / 1e6
        out["copy_lat_ms"] = [num(a.get("latency_ns")) / 1e6 for a in sorted(acks, key=lambda a: num(a.get("copy")))]
        main = next((a for a in sorted(acks, key=lambda a: num(a.get("t_ack_mono_ns"))) if a.get("ok")),
                    next((a for a in real if a.get("err_kind") != "duplicate"), first))
        out.update(err_kind=nn(main.get("err_kind")) or None, ack_ok=bool(main.get("ok")), status=main.get("status"),
                   order_id=nn(main.get("order_id")), code=num(main.get("code")))
    return out


def _books(evs: list[dict]) -> dict:
    out = {}
    for b in evs:
        a = AT.get(b.get("at"))
        if a:
            out.update({f"bk_{a}_ba": num(b.get("ba")), f"bk_{a}_bb": num(b.get("bb")), f"bk_{a}_mid": num(b.get("mid")),
                        f"bk_{a}_depth": num(b.get("depth_le_limit")), f"bk_{a}_t": num(b.get("t"))})
    return out


def build(fr: dict[str, pd.DataFrame]) -> pd.DataFrame:
    o = get(fr, "order")
    if not len(o):
        return pd.DataFrame()
    start = get(fr, "start")
    model = (start.iloc[0].get("model") or {}).get("name", "model") if len(start) and isinstance(start.iloc[0].get("model"), dict) else "model"
    sig = {r["sig"]: r for r in get(fr, "signal").to_dict("records")} if len(get(fr, "signal")) else {}
    sends, acks, fills, books = (_by(get(fr, k), "cid") for k in ("send", "ack", "fill", "book"))
    oc = {r["slug"]: num(r["outcome"]) for r in get(fr, "settle").to_dict("records")} if len(get(fr, "settle")) else {}
    rows = []
    for r in o.to_dict("records"):
        cid, s = r["cid"], sig.get(r.get("sig"), {})
        row = {"cid": cid, "sig": r.get("sig"), "slug": r.get("slug"), "up": bool(r.get("up")), "side": r.get("side"),
               "arm": f"{model}/{r.get('i_mode')}", "i": num(r.get("i")), "i_mode": r.get("i_mode"),
               "order_type": r.get("order_type"), "k": r.get("k"), "seen": num(r.get("seen")), "limit": num(r.get("limit")),
               "size": num(r.get("size")), "dry": bool(r.get("dry")), "t_decision": num(r.get("t")),
               "t_dec_mono_ns": num(r.get("t_dec_mono_ns")), "sign_us": num(r.get("sign_ns")) / 1e3,
               "build_ns": num(r.get("build_ns")), "t_signal": num(s.get("t")), "src": s.get("src"),
               "t_event_venue": num(s.get("vts")), "pu": num(s.get("pu")), "pdn": num(s.get("pdn")), "edge": num(s.get("edge")),
               "secs_left": num(s.get("secs_left")), "feat_ns": num(s.get("feat_ns")), "model_ns": num(s.get("model_ns")),
               "features": s.get("features") if isinstance(s.get("features"), dict) else {}}
        a = sorted(acks.get(cid, []), key=lambda x: num(x.get("copy")))
        for part in (_timing(sends.get(cid, []), a), _fills(fills.get(cid, []), a), _books(books.get(cid, []))):
            row.update(part)
        row["outcome"] = oc.get(r.get("slug"), math.nan)
        rows.append(row)
    return finish(pd.DataFrame(rows))


def finish(df: pd.DataFrame) -> pd.DataFrame:
    """Derived micro-report columns; paper columns NaN (a live run has no paired paper fill)."""
    df["won"] = np.where(df["up"], df["outcome"], 1 - df["outcome"])
    df["decision"] = np.where(df["sent"], "sent", "unsent")
    df["filled"] = df["fill_sh"] > 0
    df["mk10_live"] = df.get("bk_a10_mid", np.nan)
    mk = df["mk10_live"].fillna(df["won"])
    df["live_v10"] = np.where(df["filled"], df["fill_sh"] * mk - df["fill_cost"] - df["fee"], np.nan)
    df["live_vres"] = np.where(df["filled"], df["fill_sh"] * df["won"] - df["fill_cost"] - df["fee"], np.nan)
    df["t_send_ns"] = df["t_send_ns"].astype(float)
    for c in ("p_fill_sh", "p_cost", "p_fee", "p_px", "p_mk10", "paper_v10"):
        df[c] = np.nan
    df["p_filled"] = False
    return df
