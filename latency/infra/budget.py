"""Latency budget per architecture, and what each buys against the incumbents (5m BTC).

Arrival = Binance event -> order (or cancel) accepted at the CLOB origin, one way, from the
components below (each tagged measured / sourced / estimated in reports/infra-plan.md).
A taker order on these markets is held HOLD ms before it matches (taker delay, itode=true),
so its fill lands at arrival + HOLD - lead, where lead is how early the trigger fires before
the spot onset trade T0. Against run-1 bursts (first in-direction reprice on the venues'
clocks, data/out/live/events.csv.gz) and runs 1+2 burst-side taker fills
(data/out/live/speed_trades.csv.gz) this gives, per build:
  first   share of 1 bp bursts where our fill would land before the book's first reprice
  edge    net c per $ (0% fee tier) of the real taker fills within +-50 ms of that delay
  shield  maker view: share of burst-side taker $ (and of takers' winning edge) filling after
          our cancel would land, i.e. what a resting quote pulled at that time avoids

    python3 latency/infra/budget.py      (writes data/out/infra/budget.json and budget.csv)"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/out/infra"
HOLD_MS = (150, 250)  # changelog 2026-09-04 says 150; lifecycle page and OpenAPI still say 250

# one-way ms: (signal leg Binance -> decision box, decision -> order box, order box -> CLOB origin)
BUILDS = {
    "A Tokyo single host": (0.6, 0.0, 122.0),          # order via Cloudflare NRT, TTFB 242-245 / 2
    "B Dublin single host": (101.0, 0.0, 11.3),        # AWS RTT 198.5-203.6; CLOB TTFB 22-23
    "C London host, via Cloudflare": (106.0, 0.0, 9.5),  # AWS RTT 207.7-214.8; CLOB TTFB 19
    "D London colo, no Cloudflare": (106.0, 0.0, 2.0),   # estimated: same AZ, direct origin
    "E Tokyo + AWS backbone + Dublin": (0.6, 101.0, 11.3),
    "F Tokyo + McKay/BSO + Dublin": (0.6, 66.0, 11.3),   # sub-132 ms RTT claims
    "G Tokyo + McKay/BSO + London colo": (0.6, 66.0, 2.0),
    "H fiber great-circle floor + colo": (0.6, 46.9, 2.0),
}
PROC_MS = 0.4  # parse + decide + digest + secp256k1 sign + HMAC, measured fast Python path


def arrival(b: tuple[float, float, float]) -> float:
    return sum(b) + PROC_MS


def _edge_at(tr: pd.DataFrame, f_s: float, half: float = 0.05) -> tuple[float, float]:
    w = tr[(tr["delay"] > f_s - half) & (tr["delay"] <= f_s + half)]
    return (100 * w["edge"].sum() / w["usd"].sum() if w["usd"].sum() > 0 else np.nan), float(w["usd"].sum())


def table(leads_ms: dict[str, float]) -> list[dict]:
    ev = pd.read_csv(ROOT / "data/out/live/events.csv.gz")
    ev = ev[(ev["set"] == "burst1") & (ev["fam"] == "5m") & ev["ok"]].dropna(subset=["lag_server"])
    tr = pd.read_csv(ROOT / "data/out/live/speed_trades.csv.gz")
    tr = tr[tr["fam"] == "5m"]
    lag = ev["lag_server"].to_numpy()
    rows = []
    for name, b in BUILDS.items():
        a = arrival(b)
        for tname, lead in leads_ms.items():
            for hold in HOLD_MS:
                f = (a + hold - lead) / 1e3
                e, usd = _edge_at(tr, f)
                rows.append({"build": name, "trigger": tname, "hold_ms": hold, "arrival_ms": round(a, 1),
                             "fill_after_T0_ms": round(1e3 * f, 1),
                             "first_share": round(float((lag > f).mean()), 3),
                             "edge_c_per_usd": None if np.isnan(e) else round(e, 1), "usd_in_window": round(usd)})
        c = (a - leads_ms.get("spot onset", 0.0)) / 1e3
        hit = tr[(tr["delay"] > -0.5) & (tr["delay"] <= 2.0)]
        tox = hit[hit["edge"] > 0]  # fills that won for the taker = adverse selection for the maker
        rows.append({"build": name, "trigger": "maker cancel", "hold_ms": 0, "arrival_ms": round(a, 1),
                     "fill_after_T0_ms": round(1e3 * c, 1),
                     "shield_share_usd": round(float(hit.loc[hit["delay"] > c, "usd"].sum() / hit["usd"].sum()), 3),
                     "shield_share_toxic_edge": round(float(tox.loc[tox["delay"] > c, "edge"].sum() / tox["edge"].sum()), 3)})
    return rows


def main() -> None:
    leads = {"spot onset": 0.0}
    pl = OUT / "perp_lead.json"
    if pl.exists():  # head start of a perp 1 bp trigger: median and upper quartile (venue clocks)
        q = json.loads(pl.read_text())["by_thr"]["1.0"]["lead_ms_p25_p50_p75_p90"]
        leads["perp 1 bp, median lead"] = q[1]
        leads["perp 1 bp, top-quartile lead"] = q[2]
    rows = table(leads)
    (OUT / "budget.json").write_text(json.dumps(rows, indent=1))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "budget.csv", index=False)
    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(df.to_string(index=False))


if __name__ == "__main__":
    main()
