"""Maker-run sections: quoting activity, fills per hour, markouts (10 s and at resolution, c/$
with a market-bootstrap 95% CI), adverse selection (10 s markout split by whether the filled
side's pull fired within 1 s after the fill), insert / cancel ack round trips (first copy and
per copy), real vs inferred fills on the same orders (live runs), dry / live vs the simulator.
Dry runs apply no money caps: the caps a live run would have hit show as would-skips."""
from __future__ import annotations

import numpy as np
import pandas as pd

from research.predict.report.md import md

from ..stats import boot_cpd, pct
from . import load, sim


def _cpd(g: pd.DataFrame, col: str) -> tuple:
    return boot_cpd(g[col], g["cost"], g["slug"]) if len(g) else (np.nan, np.nan, np.nan)


def fills_table(f: pd.DataFrame, h: float) -> pd.DataFrame:
    out = []
    for name, g in [("all", f)] + [(s, x) for s, x in f.groupby("side")]:
        r = g[g["outcome"].notna()]
        mk, res = _cpd(g, "v10"), _cpd(r, "vres")
        out.append({"side": name, "fills": len(g), "fills_h": len(g) / h if h == h and h > 0 else np.nan,
                    "shares": g["shares"].sum(), "cost": g["cost"].sum(), "markets": g["slug"].nunique(),
                    "mk10_cpd": mk[0], "lo": mk[1], "hi": mk[2], "res_cpd": res[0], "r_lo": res[1], "r_hi": res[2],
                    "unresolved": int(g["outcome"].isna().sum())})
    return pd.DataFrame(out)


def adverse_table(f: pd.DataFrame) -> pd.DataFrame:
    out = []
    for name, g in f.groupby("pull"):
        mk = _cpd(g, "v10")
        r = g[g["outcome"].notna()]
        out.append({"after fill": name, "fills": len(g), "share": len(g) / len(f), "mk10_cpd": mk[0],
                    "lo": mk[1], "hi": mk[2], "res_cpd": _cpd(r, "vres")[0]})
    return pd.DataFrame(out)


def latency_table(o: pd.DataFrame, cp: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if len(o):
        ins = o[(o["kind"] == "insert_ack") & o.get("ok", pd.Series(False, index=o.index)).fillna(False).astype(bool)]
        can = o[o["kind"] == "cancel_ack"]
        rows += [{"ms": "insert ack (first copy)", **pct(ins.get("ms"))},
                 {"ms": "cancel ack (first copy)", **pct(can.get("ms"))},
                 {"ms": "decision to send", **pct((ins["t_send_ns"] / 1e9 - ins["t_dec"]) * 1e3 if len(ins) else [])},
                 {"ms": "lookup", **pct(o.loc[o["kind"] == "lookup", "ms"] if "ms" in o else [])}]
    for what in ("insert", "cancel"):
        c = cp[cp["what"] == what] if len(cp) else cp
        rows.append({"ms": f"{what} ack (every copy)", **pct(c["ms"] if len(c) else [])})
    if len(o) and "via" in o and o["via"].notna().any():          # --sender ab / proc
        for (kind, via), g in o[o["kind"].isin(("insert_ack", "cancel_ack"))].groupby(["kind", "via"]):
            rows.append({"ms": f"{kind.replace('_', ' ')} via {via}", **pct(g["ms"])})
    return pd.DataFrame(rows)


def activity(o: pd.DataFrame, q: pd.DataFrame, h: float) -> list[str]:
    def vc(s):
        return ", ".join(f"{k} {v}" for k, v in s.value_counts().items()) or "none"
    if not len(o):
        return [f"quote changes {len(q)}; no orders"]
    k = o["kind"]
    acks = o[k == "insert_ack"]
    ok = acks.get("ok", pd.Series(dtype=bool)).fillna(False).astype(bool)
    cans = o[k == "cancel_ack"]
    conf = cans.get("confirmed", pd.Series(dtype=bool)).fillna(False).astype(bool)
    gone = cans.get("gone", pd.Series(None, index=cans.index, dtype=object)).notna() & ~conf
    per_h = f" ({(k == 'insert').sum() / h:.0f}/h)" if h == h and h > 0 else ""
    return [f"quote changes {len(q)}, causes: {vc(q['cause']) if len(q) else 'none'}",
            f"inserts {(k == 'insert').sum()}{per_h}, accepted {int(ok.sum())}, rejected: "
            f"{vc(acks.loc[~ok, 'err_kind'].fillna('?')) if len(acks) else 'none'}",
            f"cancels {(k == 'cancel').sum()}, confirmed {int(conf.sum())}, gone (matched or expired) "
            f"{int(gone.sum())}, unconfirmed {int((~conf & ~gone).sum())}",
            f"skipped quotes (caps): {vc(o.loc[k == 'skip', 'reason']) if (k == 'skip').any() else 'none'}",
            *([f"would-skip (caps, dry only): {vc(o.loc[k == 'would_skip', 'reason'])}"]
              if (k == "would_skip").any() else [])]


def real_vs_inferred(f: pd.DataFrame, inf: pd.DataFrame) -> list[str]:
    if not len(inf) and not (len(f) and (~f["dry"].astype(bool)).any()):
        return []
    a = f.groupby("cid")["shares"].sum() if len(f) else pd.Series(dtype=float)
    b = inf.groupby("cid")["shares"].sum() if len(inf) else pd.Series(dtype=float)
    both = a.index.intersection(b.index)
    return ["Real vs inferred fills on the same orders (the simulator's maker rule, checked live):",
            f"orders filled: real {len(a)}, inferred {len(b)}, both {len(both)}; shares real {a.sum():g}, "
            f"inferred {b.sum():g}; inferred fill kinds: "
            + (", ".join(f"{k} {v}" for k, v in inf["how"].value_counts().items()) if len(inf) else "none"), ""]


def reconcile(ns: list[dict]) -> list[str]:
    """The run's last line on fills: what we booked vs the venue's trade records (fills/settle.py)."""
    r = next((x for x in reversed(ns) if x.get("kind") == "reconcile"), None)
    late = [x for x in ns if x.get("kind") == "fill_found"]
    if r is None:
        return []
    return [f"Reconcile vs the venue's trades (read {'ok' if r.get('read_ok') else 'FAILED'}): orders {r.get('orders')}, "
            f"matched orders {r.get('matched_orders')}, shares {r.get('matched_sh', 0):g}, booked != trades "
            f"{len(r.get('mismatch') or {})}, foreign trades {len(r.get('foreign_trades') or [])}, unsettled "
            f"{len(r.get('unsettled') or [])}; fills found by the trade records / user channel: {len(late)}",
            "public Data API (our wallet's TRADE rows since the start): "
            + (f"{pub['trades']} trades, {pub['shares']:g} sh, ${pub['usdc']:.2f} vs booked {r.get('booked_sh', 0):g} sh"
               if (pub := r.get("public")) else "not read"), ""]


def section(root, gamma: bool = True) -> list[str]:
    ns = load.notes(root)
    f, o, q = load.fills(root, gamma), load.frame(root, "ops"), load.frame(root, "quotes")
    h = load.hours(ns, f, q)
    start = next((r for r in ns if r.get("kind") == "trade_start"), {})
    stops = [r["reason"] for r in ns if r.get("kind") == "would_stop"]
    out = [f"{'dry (no orders)' if start.get('dry') else 'live'}, arm {start.get('arm')}, model {start.get('model')}, "
           f"{h:.2f} h, markets quoted {q['slug'].nunique() if len(q) else 0}", "", *activity(o, q, h),
           *([f"would-stop (dry only, not applied): {stops[0]}"] if stops else []), "", *reconcile(ns)]
    if len(f):
        out += ["Fills and markouts (c/$, 95% market bootstrap; maker: no fee):", "", md(fills_table(f, h), 2),
                "Adverse selection: 10 s markout by whether the filled side's pull fired within 1 s after the fill:",
                "", md(adverse_table(f), 2)]
    else:
        out += ["(no fills)", ""]
    out += ["Round trips (ms):", "", md(latency_table(o, load.copies(ns)), 1)]
    out += real_vs_inferred(f, load.frame(root, "infer"))
    out += sim.section(root, f, h, start.get("arm"))
    return out
