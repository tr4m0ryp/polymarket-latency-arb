"""Micro-run sections: live fills against the paper prediction for the same signals.

- fill rate: live fills / sent, paper fills on the same sent signals, paper on all signals;
- slippage (c): live price - paper predicted price (both filled), live - seen ask, live - limit;
- latency (ms): decision -> send (incl. signing), sign, send -> ack (incl. the 150 ms hold),
  trigger receipt -> ack, Binance event stamp -> ack (perp book / spot trade triggers);
- realised 10 s markout c/$ (market-bootstrap 95% CI), the paper's predicted c/$ on the same
  signals, the paired live - paper difference, and the trades the CI needs to exclude 0."""
from __future__ import annotations

import numpy as np
import pandas as pd

from research.predict.report.md import md

from .stats import boot_cpd, n_needed, pct

RESEARCH_CPD = 15.9   # reports/predict.md: vt_v1_m0.03_any, 251 unseen markets, L = 0


def fills_table(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for arm, g in df.groupby("arm"):
        s = g[g["sent"]]
        both = s[s["filled"] & s["p_filled"]]
        out.append({"arm": arm, "signals": len(g), "sent": len(s), "live_fills": int(s["filled"].sum()),
                    "live_fill_rate": s["filled"].mean() if len(s) else np.nan,
                    "paper_fill_rate_sent": s["p_filled"].mean() if len(s) else np.nan,
                    "paper_fill_rate_all": g["p_filled"].mean(),
                    "slip_vs_paper_c": 100 * (both["px"] - both["p_px"]).mean() if len(both) else np.nan,
                    "px_minus_seen_c": 100 * (s["px"] - s["seen"]).mean() if s["filled"].any() else np.nan,
                    "px_minus_limit_c": 100 * (s["px"] - s["limit"]).mean() if s["filled"].any() else np.nan})
    return pd.DataFrame(out)


def latency_table(df: pd.DataFrame) -> pd.DataFrame:
    s = df[df["sent"] & df["t_ack_ns"].notna()]
    rows = {"decision_to_send": (s["t_send_ns"] / 1e9 - s["t_decision"]) * 1e3,
            "sign": s["sign_us"] / 1e3,
            "send_to_ack": (s["t_ack_ns"] - s["t_send_ns"]) / 1e6,
            "receipt_to_ack": (s["t_ack_ns"] / 1e9 - s["t_signal"]) * 1e3}
    bn = s[s["src"].isin(["pb", "st"])]
    rows["binance_event_to_ack"] = (bn["t_ack_ns"] / 1e9 - pd.to_numeric(bn["t_event_venue"], errors="coerce")) * 1e3
    return pd.DataFrame([{"ms": k, **pct(v)} for k, v in rows.items()])


def markout_table(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    rows, notes = [], []
    for arm, g in df.groupby("arm"):
        s = g[g["sent"]]
        lf, pf = s[s["filled"]], s[s["p_filled"]]
        both = s[s["filled"] & s["p_filled"]]
        live = boot_cpd(lf["live_v10"], lf["fill_cost"], lf["slug"])
        paper = boot_cpd(pf["paper_v10"], pf["p_cost"], pf["slug"])
        d = both["live_v10"] / both["fill_cost"] - both["paper_v10"] / both["p_cost"]
        diff = boot_cpd(d * both["fill_cost"], both["fill_cost"], both["slug"])
        res = boot_cpd(lf["live_vres"], lf["fill_cost"], lf["slug"])
        x = 100 * lf["live_v10"] / lf["fill_cost"]
        sd = float(x.std(ddof=1)) if len(x) > 1 else np.nan
        px = 100 * pf["paper_v10"] / pf["p_cost"]
        rows.append({"arm": arm, "live_fills": len(lf), "markets": lf["slug"].nunique(),
                     "live_mk10_cpd": live[0], "lo": live[1], "hi": live[2],
                     "paper_mk10_cpd": paper[0], "p_lo": paper[1], "p_hi": paper[2],
                     "live_minus_paper": diff[0], "d_lo": diff[1], "d_hi": diff[2], "live_res_cpd": res[0],
                     "sd_per_fill": sd, "n_at_live_mean": n_needed(sd, float(x.mean()) if len(x) else np.nan),
                     "n_at_paper_mean": n_needed(sd, float(px.mean()) if len(px) else np.nan),
                     "n_at_research": n_needed(sd, RESEARCH_CPD)})
        if len(lf) and live[1] == live[1]:
            notes.append(f"{arm}: live 10 s markout CI [{live[1]:+.1f}, {live[2]:+.1f}] c/$ "
                         f"{'excludes' if live[1] > 0 or live[2] < 0 else 'includes'} 0 after {len(lf)} fills.")
    return pd.DataFrame(rows), notes


def section(df: pd.DataFrame) -> list[str]:
    skip = df.loc[~df["sent"], "decision"].value_counts()
    errs = df.loc[df["sent"], "err_kind"].fillna("ok").value_counts() if "err_kind" in df else pd.Series(dtype=int)
    mk, notes = markout_table(df)
    out = [f"signals {len(df)}, sent {int(df['sent'].sum())}, live fills {int(df['filled'].sum())}, "
           f"unresolved {int(df['outcome'].isna().sum())}", "",
           "Skipped signals: " + (", ".join(f"{k} {v}" for k, v in skip.items()) or "none"),
           "Venue results of sent orders: " + (", ".join(f"{k} {v}" for k, v in errs.items()) or "none"), "",
           "Fills, live vs paper on the same signals:", "", md(fills_table(df), 3),
           "Latency (ms):", "", md(latency_table(df), 1),
           "10 s markout c/$ (95% market bootstrap) and trades needed for the CI to exclude 0 "
           f"(n = (1.96 sd / mean)^2 with the live per-fill sd; research reference +{RESEARCH_CPD} c/$):",
           "", md(mk, 2), *notes]
    return out
