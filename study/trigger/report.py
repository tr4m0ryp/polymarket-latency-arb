"""Markdown write-up for the price-trigger study (numbers filled from run.py)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def md(df: pd.DataFrame, digits: int = 3) -> str:
    df = df.copy()
    for c in df.columns:
        if pd.api.types.is_float_dtype(df[c]):
            df[c] = df[c].map(lambda v: "" if pd.isna(v) else f"{v:,.{digits}f}")
    cols = [str(c) for c in df.columns]
    rows = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    rows += ["| " + " | ".join(str(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(rows)


def _peak(s: pd.Series) -> tuple[int, float]:
    i = int(s.idxmax())
    return i, float(s.loc[i])


def headline(slug: str, r: dict) -> str:
    bt = r["bot_table"].set_index("wallet")
    ab, ot = bt.loc["all_bots"], bt.loc["other_takers"]
    j, acc = _peak(r["lag_accuracy"]["all_bots"])
    k, _ = _peak(r["xcorr"]["all_bots"])
    kb, _ = _peak(r["xcorr"]["book_last_print"])
    es = r["event_stats"]
    gc = r["gap_curve"]
    em = r["edge_by_move"]
    lo, hi = em.iloc[0], em[em["bin"].astype(str).str.startswith(("(1.0", "(2.0", "(4.0"))]
    hi_pnl = 100 * (hi["pnl_per_usd_c"] * hi["usd"]).sum() / hi["usd"].sum() / 100
    bp_usd = r["btc_level"] / 1e4
    return "\n".join([
        f"**{slug}** ({r['markets']} markets, {len(r['bots'])} latency_arb wallets, BTC about ${r['btc_level']:,.0f}, so 1 bp is about ${bp_usd:.2f}):",
        f"- **Trigger second:** the bots' side matches the Binance move of the single second {j} s before the fill's block time in {acc:.1%} of USD (other takers {r['lag_accuracy']['other_takers'].loc[j]:.1%}); seconds 6-8 back average {r['lag_accuracy']['all_bots'].loc[6:8].mean():.1%}.",
        f"- **Speed:** bot flow peaks {k} s after the Binance second (cross-correlation), the YES last print peaks at {kb} s. After a >= 3 bp jump ({es['n_events']} events) a bot fills on the jump side within 6 s in {es['hit_within_6s']:.0%} of cases vs {es['hit_within_6s_random']:.0%} at random seconds; median first fill {es['first_fill_lag_median']:.0f} s (IQR {es['first_fill_lag_p25']:.0f}-{es['first_fill_lag_p75']:.0f} s).",
        f"- **Book staleness gates firing:** after a >= 2 bp 2 s move the top-5 bots fire in {gc['fire_rate'].iloc[1:3].min():.0%}-{gc['fire_rate'].iloc[1:3].max():.0%} of seconds when the book already sits within 2 c of fair, {gc['fire_rate'].iloc[-1]:.0%} when fair is > 10 c ahead of the book (direction right {gc['dir_accuracy'].iloc[-1]:.0%}).",
        f"- **Edge per trade:** pooled bot taker fills pay {ab['paid']:.3f} for a side worth {ab['fair_side']:.3f} under the spot model, {ab['edge_c']:.2f} c/share; realized {ab['pnl_per_usd_c']:.2f} c per USD, 2 s markout {ab['mo2_per_usd_c']:.2f} c per USD, median fill ${ab['med_fill_usd']:.0f} (other takers: {ot['edge_c']:.2f} c/share, {ot['pnl_per_usd_c']:.2f} c per USD).",
        f"- **Edge sits in the triggered fills:** fills after an aligned 3 s move > 1 bp earn {hi_pnl:.1f} c per USD on {hi['usd_share'].sum():.0%} of bot USD; fills against a > 1 bp move earn {lo['pnl_per_usd_c']:.1f} c per USD.",
        f"- **Background rate:** with no move (|2 s move| < 0.25 bp) the top-5 bots still take in {r['fire_curve']['fire_rate'].iloc[0]:.0%} of seconds at direction accuracy {r['fire_curve']['dir_accuracy'].iloc[0]:.0%}; a >= 2 bp move lifts that to {r['fire_curve']['fire_rate'].iloc[4:].max():.0%} at {r['fire_curve']['dir_accuracy'].iloc[4]:.0%}.",
    ])


def section(slug: str, r: dict) -> str:
    la = r["lag_accuracy"].T.reset_index().rename(columns={"index": "wallet"})
    la.columns = [str(c) if c == "wallet" else f"j={c}" for c in la.columns]
    xc = r["xcorr"].loc[-2:8].T.reset_index().rename(columns={"index": "series"})
    xc.columns = [str(c) if c == "series" else f"k={c}" for c in xc.columns]
    ev = r["event_study"].loc[-2:10].reset_index()
    bt = r["bot_table"]
    return "\n\n".join([
        f"## {slug}",
        "### Who and what they pay (live taker fills)",
        md(bt[["wallet", "fills", "usd", "med_fill_usd", "paid", "fair_side", "edge_c", "edge_pos_share",
               "pnl_per_usd_c", "mo2_per_usd_c", "mo10_per_usd_c"]], 3),
        "### Spot state at the fill (moves signed by the side taken; Brier of fair and of the prior print against the outcome, YES frame)",
        md(bt[["wallet", "r3_al_bp", "move_open_al_bp", "move_open_al_usd", "secs_left_med",
               "brier_fair", "brier_book"]], 3),
        "### Which candidate trigger the side follows (USD share matching sign)",
        md(r["feature_accuracy"], 3),
        "### Which Binance second the side follows (j = seconds before the fill's block ts)",
        md(la, 3),
        "### Cross-correlation, signed taker USD at t+k vs Binance 1 s return at t",
        md(xc, 3),
        f"### Event study: mean jump-aligned USD / book change at t+k after a >= 3 bp 2 s jump\n\n{r['event_stats']}",
        md(ev, 3),
        "### Fire curve (top 5 bots): fire rate in [u+1, u+3] by |2 s move| known at u",
        md(r["fire_curve"].astype({"m_bin": str}), 3),
        "### Gap curve: |move| >= 2 bp, by fair - book in the move's direction",
        md(r["gap_curve"].astype({"gap_bin": str}), 3),
        "### Edge by aligned 3 s move at the fill (all bots pooled)",
        md(r["edge_by_move"].astype({"bin": str}), 2),
        "### PnL decomposition (all fills): locked Up+Down pairs vs residual directional",
        md(r["decompose"], 2),
    ])


INTRO = """# What triggers the BTC latency bots

Data: BTC Up/Down 5m and 15m fills (about 2 days), Binance BTCUSDT 1 s closes.
Bot set: every `latency_arb` row of `data/out/latency/wallets.csv` for the family.
Code: `study/trigger/` (`python3 study/trigger/run.py`). Tables
also as CSV under `data/out/latency/trigger/`.

Conventions: fill `ts` is the Polygon block timestamp, which lags the off-chain
match. S[t] is the Binance close of second [t, t+1). A move "j s before the fill"
is log(S[ts-j]/S[ts-j-1]). `fair` is P(Up) from driftless Brownian spot with the
trailing 300 s vol under the real settlement rule; `book` is the last YES print
before the fill; `edge` = fair value of the side taken minus price paid.

## Resolution source

Gamma description (5m and 15m): resolves Up if the Chainlink BTC/USD 60 s TWAP
data stream at the end of the range is >= the value at its start
(https://data.chain.link/streams/btc-usd-twap-60s-streams), "not according to
any other sources or spot markets". A Binance 60 s TWAP proxy reproduces
{agree5:.1%} (5m) and {agree15:.1%} (15m) of outcomes. The Chainlink stream
itself needs Data Streams credentials, so a direct Binance-vs-Chainlink lead
was not measured. Structurally Binance leads the settlement number: a 60 s
TWAP lags spot by about 30 s on average, and Binance is one of the venues the
aggregate is built from. What was measured is that Binance leads the
Polymarket book by about 4 s (cross-correlation below).

## Answer

"""

RULE = """
## Decision rule (reconstructed)

1. Watch Binance BTCUSDT (or an equivalent fast feed) tick by tick.
2. When BTC moves, recompute P(Up) for the live market from the spot vs the
   strike, seconds left and short-term vol.
3. If the Polymarket ask on the side the move favours is still below that
   value (the book has not repriced), take it with a marketable buy, small
   size ($10-$30 a fill), and repeat on every further tick.
4. When spot reverses, buy the other side the same way. The top wallets
   never sell (taker buy share 1.00); they hold to resolution. Matched
   Up+Down pairs cost 0.95-1.08 per pair (decomposition table). For
   0xc53375ff94e96100f2b30a4b5775db35218d69a9 the pairs wash (-$204) and
   the residual exposure from the latest moves carries all of the +$20.9k;
   0x3048d65321be3497164cdfc2996f94f98a2e7537 gets $9.4k of its $20.7k from
   pairs at 0.99. In 15m, 0x32ed2e546b187ca15e2841edc82b22c713cf8ec3 and
   0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed get about half their PnL from
   pairs bought at 0.95 with about 60% maker USD;
   0x3725d52f3c252e8374999cc8617292ea2608ad88 shares their fingerprint
   (same fill size, price paid and maker share) but its pairs wash.

The bots are not purely event-driven: they take continuously at a background
rate and lean with spot; a fresh move raises both the rate and the direction
accuracy.

The signal is the Binance move itself, not the cumulative move since open:
direction tracks the second about 3 s before the block time, the bots fire
more when the move is larger and much more when the book still lags fair, and
the edge per fill grows with the size of the aligned move. Copying fails
because the edge is a 2-4 s repricing window that a follower reading on-chain
fills sees only after it closed.
"""


def write_report(res: dict, path: Path) -> None:
    s5, s15 = res["btc-up-or-down-5m"], res["btc-up-or-down-15m"]
    text = INTRO.format(agree5=s5["spot_outcome_agree"], agree15=s15["spot_outcome_agree"])
    text += "\n\n".join(headline(k, v) for k, v in res.items()) + "\n" + RULE + "\n"
    text += "\n\n".join(section(k, v) for k, v in res.items()) + "\n"
    path.write_text(text)
    print(f"wrote {path}")
