"""Hold-test sections: POST ack by order type and role (marketable at the ask vs the unfillable
post-only control), ack status mix, `delayed` follow-up times, spend; and the duplicate-send
test (accepted copies per payload, distinct order ids, first-ack vs single-copy round trip)."""
from __future__ import annotations

import pandas as pd

from research.predict.report.md import md

from .stats import pct


def section(df: pd.DataFrame) -> list[str]:
    if not len(df):
        return ["(no hold-test cycles)"]
    s = df[df.get("decision", pd.Series(dtype=str)) == "sent"].copy()
    skips = df.loc[df["decision"] != "sent", "decision"].value_counts()
    out = [f"orders {len(s)} (marketable {int((s['role'] == 'marketable').sum())}, control "
           f"{int((s['role'] == 'control').sum())}), filled {int((s['fill_sh'] > 0).sum())}, "
           f"spent ${s['spent'].sum():.2f}",
           "Skipped: " + (", ".join(f"{k} {v}" for k, v in skips.items()) or "none"), ""]
    if not len(s):
        return out
    lat = [{"role": r, "type": t, **pct(g["ack_ms"])} for (r, t), g in s.groupby(["role", "type"])]
    out += ["POST ack by role and order type (ms):", "", md(pd.DataFrame(lat), 1), ""]
    st = (s.groupby(["role", "type", "status_ack"])["ack_ms"].agg(["count", "median"])
          .reset_index().rename(columns={"count": "n", "median": "ack_p50_ms"}))
    out += ["Ack status (the venue's first answer) and its round trip:", "", md(st, 1), ""]
    if "hold_ms" in s and s["hold_ms"].notna().any():
        d = [{"type": t, **pct(g["hold_ms"])} for t, g in s[s["hold_ms"].notna()].groupby("type")]
        out += ["`delayed` orders, send to first non-delayed status (ms, one poll coarse):", "", md(pd.DataFrame(d), 1), ""]
    ctrl = s.loc[s["role"] == "control", "ack_ms"].median()
    for t, g in s[s["role"] == "marketable"].groupby("type"):
        out.append(f"{t}: marketable ack p50 {g['ack_ms'].median():.0f} ms vs control {ctrl:.0f} ms "
                   f"(+{g['ack_ms'].median() - ctrl:.0f} ms), n {len(g)}")
    return out


def dup_section(df: pd.DataFrame) -> list[str]:
    if not len(df):
        return ["(no duplicate-send repetitions)"]
    s = df[df["decision"] == "sent"]
    rows = []
    for k, g in s.groupby("k"):
        copies = [c for cs in g["copies"] for c in cs]
        extra = pd.Series([c.get("err_kind") or c.get("status") for cs in g["copies"] for c in cs[1:]] or [None])
        rows.append({"k": k, "reps": len(g), "accepted_per_payload": g["accepted"].mean(),
                     "max_distinct_ids": int(g["distinct_ids"].map(len).max()),
                     "first_ack_p50_ms": g["first_ack_ms"].median(),
                     "copy_ack_p50_ms": pct([c["ms"] for c in copies])["p50"],
                     "first_ack_p90_ms": pct(g["first_ack_ms"])["p90"],
                     "other_copies": ", ".join(f"{a} {b}" for a, b in extra.dropna().value_counts().items()) or "-"})
    safe = all(r["max_distinct_ids"] <= 1 for r in rows)
    return [f"Duplicate copies {'deduplicated (one order per payload)' if safe else 'NOT deduplicated: unsafe'}", "",
            md(pd.DataFrame(rows), 1)]
