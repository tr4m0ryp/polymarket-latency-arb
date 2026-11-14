"""Write reports/live-lead.md from the event rows."""
from __future__ import annotations

import pandas as pd

import stats


def _md(df: pd.DataFrame, fmt: str = "{:.3g}") -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for r in df.itertuples(index=False):
        out.append("| " + " | ".join(fmt.format(v) if isinstance(v, float) else str(v) for v in r) + " |")
    return "\n".join(out)


def write_report(ev: pd.DataFrame, meta: dict, out_dir, path) -> None:
    lt, pr = stats.lead_table(ev), stats.profile(ev)
    dmo, dmd = stats.depth_table(ev, "mo"), stats.depth_table(ev, "mdl")
    tk = stats.taken_table(ev)
    for name, df in (("taken", tk), ("lead", lt), ("profile", pr), ("depth_mo", dmo), ("depth_mdl", dmd)):
        df.to_csv(out_dir / f"{name}.csv", index=False)
    bm = {f: stats.by_move(ev, f) for f in ("5m", "15m")}
    ch = meta["chainlink"]
    xc = ", ".join(f"{k}:{v:.2f}" for k, v in ch["xcorr"].items() if -2 <= int(k) <= 6)
    txt = f"""# Live lead and stale depth (auto-generated tables)

Recorded {meta['hours']:.2f} h; markets 5m {meta['markets']['5m']}, 15m {meta['markets']['15m']}.
Receipt delay (our SNTP clock minus venue stamp, median): Binance {meta['binance_recv_delay_s']*1e3:.0f} ms,
CLOB 5m {meta['clob_recv_delay_s']['5m']*1e3:.0f} ms, 15m {meta['clob_recv_delay_s']['15m']*1e3:.0f} ms.
Events kept after the backlog/gap filter (Binance lag <= 0.3 s, CLOB lag <= 0.1 s, no reconnect within 5 s):
{meta['kept_share']}. Reconnect gaps per market: {sum(meta['gaps'].values())} over {len(meta['gaps'])} markets.

## Chainlink vs Binance
Peak xcorr lag {ch['peak_lag_s']} s (positive = Chainlink after Binance), weighted mean {ch['mean_lag_s']:.2f} s;
observation-to-push {ch['push_delay_s']:.2f} s, push-to-receipt {ch['recv_delay_s'] - ch['push_delay_s']:.2f} s;
basis Binance minus Chainlink {ch['basis_usd']:.1f} USD. xcorr by lag: {xc}.

## Book reaction after a Binance burst (receipt clock)
{_md(lt)}

## Catch-up profile (fraction of the final move priced in, receipt clock, offset from R0)
{_md(pr)}

## Stale depth, fair = book mid 3 s later (USD; edge net of taker fee at 0% tier)
{_md(dmo)}

## What takers actually captured, [R0 - 0.5, R0 + 2] s (per event, USD)
{_md(tk)}

## Stale depth, fair = pre-burst mid + spot-model change
{_md(dmd)}

## By Binance move over [R0 - 1.2, R0 + 5] s (bp), bursts >= 1 bp
5m
{_md(bm['5m'])}

15m
{_md(bm['15m'])}
"""
    path.write_text(txt)
