"""Run-level report sections: header, signals / vetoes / skips, errors, latency."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from research.predict.report.md import md

from btclat.trade.report.stats import pct

from .load import get


def _counts(s: pd.Series) -> str:
    s = s.fillna("-").astype(str).value_counts()
    return ", ".join(f"{k} {v}" for k, v in s.items()) or "none"


def header(fr: dict[str, pd.DataFrame], run: str) -> list[str]:
    out = [f"# Rust bot run {run}", ""]
    for e in get(fr, "start").to_dict("records"):
        m = e.get("model") if isinstance(e.get("model"), dict) else {}
        out += [f"Start: mode {e.get('mode')}, i_mode {e.get('i_mode')} (i {e.get('i')}, set {e.get('i_set')}), model "
                f"{m.get('name')} {m.get('sha16')} ({m.get('n_trees')} trees), host {e.get('host')}, version {e.get('version')}",
                f"Args: `{json.dumps(e.get('args'), sort_keys=True)}`; limits: `{json.dumps(e.get('limits'), sort_keys=True)}`", ""]
    if not len(get(fr, "start")):
        out += ["(no start event)", ""]
    stops = get(fr, "stop").to_dict("records")
    for e in stops:
        out.append(f"Stop: {e.get('reason')}; cancel-all ok {e.get('cancel_all_ok')}")
    if not stops:
        out.append("Stop: none logged (killed or still running)")
    ca = get(fr, "cancel")
    if len(ca):
        out.append(f"Cancels: {len(ca)}, ok {int(ca['ok'].fillna(False).astype(bool).sum())}")
    ls = get(fr, "log_stats")
    if len(ls):
        l = ls.iloc[-1]
        out.append(f"Logger: written {int(l.get('written', 0))}, dropped {int(l.get('dropped', 0))}, io_errors {int(l.get('io_errors', 0))}")
    return out + [""]


def signals(fr: dict[str, pd.DataFrame]) -> list[str]:
    sg = get(fr, "signal")
    if not len(sg):
        return ["(no signals)", ""]
    sk = get(fr, "skip")
    out = [f"Signals {len(sg)}: " + _counts(sg["decision"]), ""]
    for d, title in (("veto", "Vetoes"), ("skip", "Skips")):
        x = sg[sg["decision"] == d]
        if len(x):
            out.append(f"{title} by reason: " + _counts(x["reason"]))
    if len(sk):
        out.append("Skip events by reason: " + _counts(sk["reason"]))
    o = get(fr, "order")
    out.append(f"Orders {len(o)} (dry {int(o['dry'].fillna(False).astype(bool).sum()) if len(o) else 0})")
    return out + [""]


def errors(fr: dict[str, pd.DataFrame], df: pd.DataFrame) -> list[str]:
    er = get(fr, "error")
    out = []
    if len(df):
        out.append("Venue result of the main ack per sent order: " + _counts(df.loc[df["sent"], "err_kind"].fillna("ok")))
    ac = get(fr, "ack")
    if len(ac):
        ek = ac["err_kind"] if "err_kind" in ac else pd.Series(["ok"] * len(ac))
        code = ac["code"] if "code" in ac else pd.Series([None] * len(ac))
        out.append("All copies by err_kind: " + _counts(ek.fillna("ok")) + "; http codes: " + _counts(code))
    if len(er):
        out += ["", f"Errors {len(er)}:", "", md(er.groupby(["where", "err"]).size().rename("n").reset_index(), 0)]
    else:
        out.append("Errors: none")
    return out + [""]


def latency(fr: dict[str, pd.DataFrame], df: pd.DataFrame) -> list[str]:
    ac = get(fr, "ack")
    out = []
    if len(df) and df["sent"].any():
        s = df[df["sent"]]
        rows = {"first_ack (first send -> earliest ack)": s["first_ack_ms"],
                "decision_to_send (mono)": (s["t_send_mono_ns"] - s["t_dec_mono_ns"]) / 1e6}
        out += ["Ack latency, first copy (ms):", "", md(pd.DataFrame([{"ms": k, **pct(v)} for k, v in rows.items()]), 1)]
    if len(ac):
        rows = [{"copy": c, **pct(g["latency_ns"] / 1e6)} for c, g in ac.groupby("copy")]
        out += ["Ack latency per copy (ms, each copy's own round trip):", "", md(pd.DataFrame(rows), 1)]
    if len(df):
        ns = {"feature": df["feat_ns"], "model": df["model_ns"], "build": df["build_ns"], "sign": df["sign_us"] * 1e3}
        out += ["Bot internal (us):", "", md(pd.DataFrame([{"stage": k, **pct(v, 1e-3)} for k, v in ns.items()]), 1)]
    return out or ["(no acks)", ""]
