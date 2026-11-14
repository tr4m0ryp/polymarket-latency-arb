"""Write data/out/predict/improve/diag-loss-anatomy.md from the analysis tables (numbers are read
from the tables; the prose states what they show)."""
from __future__ import annotations

import pandas as pd

from ... import OUT
from . import tables as T
from .text import HEAD, HYPOTHESES, IDEAS, METHOD


def _pick(df: pd.DataFrame, **kw) -> pd.Series:
    m = pd.Series(True, index=df.index)
    for k, v in kw.items():
        m &= df[k] == v
    return df[m].iloc[0]


def verdict(t: dict) -> str:
    d, a, bins, win = t["decomp"], t["auc"], t["delta_bins"], t["delta_windows"]
    w = _pick(d, arm="taker1s", L=0, lose=0.0)
    lo = _pick(d, arm="taker1s", L=0, lose=1.0)
    keys = ["taker1s_L0", "veto_L0", "taker1s_L-40", "veto_L-40"]
    da = a[a["var"] == "delta"].iloc[0]
    low = bins[bins["delta_bin"].str.startswith("(0.0, 3.0") & bins["arm"].isin(["taker1s", "veto"])]
    ext = win[(win["window"] == "ext") & (win["arm"] != "micf")]
    quiet = win[(win["window"] != "ext") & (win["arm"] != "micf")]
    g = t["delta_grid"][t["delta_grid"]["picked"]]
    dep = bins[bins["arm"].isin(["taker1s", "veto"])]
    cr = t["calib_regime"][t["calib_regime"]["L"] == 0]
    ce = cr[(cr["regime"] == "ext (busy)") & cr["delta_bin"].str.startswith("(0.0, 3.0")].iloc[0]
    cq = cr[(cr["regime"] != "ext (busy)") & cr["delta_bin"].map(lambda b: float(b.split(",")[0][1:]) >= 8)]
    gl = "; ".join(f"{r.arm} L{r.L}: thr {r.thr:g}, {r.read_gain_day:+,.0f} [{r.read_lo:+,.0f}, {r.read_hi:+,.0f}]"
                   for r in g.itertuples())
    return f"""## Verdict

- **Losers are reversals, not costs:** winners and losers pay the same half spread, book walk,
  fee and hold drift; the whole gap is the venue move after the match (1 s taker, L = 0:
  {w.d_move:+.1f} vs {lo.d_move:+.1f} c/sh). No execution-side change (limit, size, slippage) separates them.
- **One consistent separator, the settlement delta** (cents of the bought token per bp of BTC,
  `model/derive.py`): AUC for "fill loses" {min(da[k] for k in keys):.2f}-{max(da[k] for k in keys):.2f} on the deployed arms, below
  0.5 in every arm x L x window cell. Fills at delta <= 3 c/bp: {low['c_usd'].min():+.1f} to {low['c_usd'].max():+.1f} c/$,
  {low['lose'].min():.0%}-{low['lose'].max():.0%} losers; delta > 12 earns +10 to +28 c/$.
- **The model is flat across delta, the market is not:** predicted value at the fills stays at
  {dep['pred_c'].min():.1f}-{dep['pred_c'].max():.1f} c/sh in every delta bin while the realized 10 s markout runs from
  {dep['mk10_c_sh'].min():+.1f} to {dep['mk10_c_sh'].max():+.1f} c/sh. Row level (every decision row with pred >= 3 c, best level, no
  simulator, L = 0): in ext the model over-predicts in every delta bin, worst at delta <= 3
  ({ce.pred_c:.1f} c predicted, {ce.real_1s_c:+.1f} c realized at 1 s); in the quiet windows it under-predicts at
  delta >= 8 ({cq['pred_c'].min():.1f}-{cq['pred_c'].max():.1f} c predicted, {cq['real_1s_c'].min():.1f}-{cq['real_1s_c'].max():.1f} c realized) and low-delta rows are not
  clearly over-predicted (few markets).
- **The busy extension is a low-delta regime:** median fill delta {ext['delta_median'].min():.1f}-{ext['delta_median'].max():.1f} c/bp in ext vs
  {quiet['delta_median'].min():.0f}-{quiet['delta_median'].max():.0f} elsewhere; {ext['share_delta<5'].min():.0%}-{ext['share_delta<5'].max():.0%} of ext fills below 5 c/bp vs <= {quiet['share_delta<5'].max():.0%} elsewhere.
  The fire-rate jump in ext is mostly these fills. On top, ext under-delivers in every delta bin.
- **No gate chosen on select can see it:** select has 0-2% low-delta fills. A delta floor picked on
  select + dev3 and read on test3 run 1 + ext (fill-drop approximation, not a re-simulation):
  {gl} $/day. It drops nothing in select or test3 run 1.
- **Everything else is weak or two-faced:** price level separates how often a fill loses (cheap
  tokens), not dollars; Binance message rate acts only through vol; burst position, own history,
  time to expiry and adding to a losing fill do not separate consistently; requiring Polymarket
  staleness removes the 1 s taker's early-entry edge (-$300 to -$920/day in every window).
- **Worst markets are one-offs:** the single worst (test3 run 1, 10:40 UTC) is a pinned BTC with
  the strike at spot (delta 200-280 c/bp): five Up buys in 1.4 s at 62 s to expiry with no Binance
  signal while the Up mid fell 0.77 -> 0.07. Market regime separates losing markets weakly.
"""


def write(t: dict, f: pd.DataFrame, nmk: dict) -> None:
    s = [HEAD.format(n=len(f), mk=sum(nmk.values())), verdict(t), METHOD]
    s += ["## 1. Arms on the allowed windows (10 s markout c/$ / fills per day)\n", T.overview(t["overview"])]
    s += ["## 2. Winners vs losers: c per share of each markout part\n",
          "`d_move` = venue mid 10 s after the match minus the mid at the match; `d_half` = mid minus ask at "
          "the match; `d_walk` = ask at the match minus the fill VWAP; `d_hold` = ask drift during the hold.\n",
          T.decomp(t["decomp"])]
    s += ["## 3. What separates losing fills (AUC for \"fill loses\", market bootstrap 95% CI, windows on the same side)\n",
          "AUC > 0.5: higher values lose more often. Signed variables point toward the side bought.\n",
          T.auc(t["auc"])]
    s += ["### Settlement delta: 10 s markout c/$ by bin (fills, share in ext)\n", T.delta_bins(t["delta_bins"])]
    s += ["### Low-delta share by window: median delta / share < 5 c/bp / low-delta fills per day\n",
          T.delta_windows(t["delta_windows"])]
    s += ["### Row-level calibration, L = 0 (every decision row with pred >= 3 c; best level, no rivals)\n",
          T.calib(t["calib_regime"], 0)]
    s += ["### By hour, L = 0, test3 run 1 and ext: c/$ (fills, median delta)\n", T.hours(t["hour"])]
    s += ["### Under the 50 ms competition sensitivity (test3 run 1, L = 0): c/$ (fills) by delta bin\n",
          T.comp(t["delta_comp"])]
    sh = t["shared"]
    s += ["## 4. Worst markets\n", T.tails(t["tails"]),
          f"\nPer-market markout correlates across arms (Spearman {sh['spearman'].min():.2f}-{sh['spearman'].max():.2f}), "
          "so bad markets are partly shared; whole-market regime (vol, message rate, Polymarket range and "
          "spread) separates losing markets with AUC <= 0.64 (`regime_auc.csv`). Worst markets of the 1 s "
          "taker at L = 0 (f_ = mean over its fills, m_range_c = Polymarket mid range in the market):\n",
          T.worst(t["worst_taker_L0"])]
    sc = t["screen_select"]
    s += ["## 5. Can a gate be selected?\n",
          f"Select-chosen tail cuts (10-30% of any of {sc['var'].nunique()} decision-time variables, read on dev3 + test3 "
          f"run 1 + ext): {int((sc['fit_gain_day'] > 0).sum())} of {len(sc)} add any markout on select, "
          f"{int((sc['read_lo'] > 0).sum())} have an unseen CI above 0. On select nearly every tail of every variable is "
          "net positive: the losing states are almost absent there.\n\n"
          "Delta floor picked on select + dev3, read on test3 run 1 + ext ($/day of dropped fills' markout, "
          "market bootstrap; ignores knock-on effects on later orders):\n", T.gate_grid(t["delta_grid"]),
          "\nRules read window by window (round thresholds chosen after seeing all windows: diagnostic):\n",
          T.rules(t["rules"])]
    s += [IDEAS, HYPOTHESES]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "diag-loss-anatomy.md").write_text("\n".join(s))
