"""Load a series' fills into one frame expressed in the market's YES frame.

Every binary fill is rewritten as a signed quantity of outcome-0 shares:
buying outcome 1 at p is economically selling outcome 0 at 1-p. Then a
fill's hold-to-resolution value is  q * (R - pi), with
  q   signed outcome-0 shares (+ long, - short),
  pi  implied outcome-0 price of the fill,
  R   1 if outcome 0 won else 0.
Summing q*(R-pi) over a wallet's fills is its exact trading PnL in that
market, splits and merges included (both are zero-PnL at par)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .collect import RAW


def load_markets(slug: str) -> pd.DataFrame:
    rows = [json.loads(line) for line in open(RAW / slug / "markets.jsonl")]
    # newly closed events shift Gamma's pages while paging, so dedupe
    mk = pd.DataFrame(rows).drop_duplicates("condition_id")
    mk["R"] = (mk["winner"] == 0).astype(float)
    return mk.set_index("condition_id")


def load_fills(slug: str, mk: pd.DataFrame | None = None) -> pd.DataFrame:
    mk = load_markets(slug) if mk is None else mk
    f = pd.read_csv(RAW / slug / "fills.csv.gz",
                    dtype={"wallet": str, "tx": str, "name": str, "pseudonym": str})
    f = f[f["condition_id"].isin(mk.index)].drop_duplicates(
        ["condition_id", "tx", "wallet", "outcome_index", "side", "size", "price"]).copy()
    buy = np.where(f["side"] == "BUY", 1.0, -1.0)
    yes = f["outcome_index"] == 0
    f["q"] = np.where(yes, buy, -buy) * f["size"]
    f["pi"] = np.where(yes, f["price"], 1.0 - f["price"])
    f["usd"] = f["size"] * f["price"]
    f["R"] = f["condition_id"].map(mk["R"])
    f["event"] = f["condition_id"].map(mk["event_slug"])
    f["pnl"] = f["q"] * (f["R"] - f["pi"])
    start = f["condition_id"].map(mk["start_ts"]).astype(float)
    end = f["condition_id"].map(mk["end_ts"]).astype(float)
    # position of the fill inside the market's live window: <0 before it opens
    f["t_rel"] = (f["ts"] - start) / (end - start).clip(lower=1)
    f["end_ts"] = end
    f["secs_to_end"] = end - f["ts"]
    return f.sort_values("ts", kind="stable").reset_index(drop=True)


def slugs() -> list[str]:
    return sorted(p.name for p in RAW.iterdir()
                  if (p / "fills.csv.gz").exists() and not p.name.startswith("_"))


def load_all(names: list[str] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    fs, ms = [], []
    for s in names or slugs():
        mk = load_markets(s)
        fl = load_fills(s, mk)
        fl["series"] = s
        fs.append(fl)
        ms.append(mk)
    return pd.concat(fs, ignore_index=True), pd.concat(ms)


def raw_dir(slug: str) -> Path:
    return RAW / slug
