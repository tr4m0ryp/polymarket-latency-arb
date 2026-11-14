"""Parse every complete recorded hour into data/cache/hidden/prep/<hour>.pkl (dict of tables).

    nice -n 10 python3 study/hidden/prep/run.py [hour ...]

Two worker processes at most (shared machine); an hour already parsed is skipped. Hours covered by
the side recorder (study/hidden/venues.py) also get perp trades, Coinbase, OKX and Bybit."""
from __future__ import annotations

import sys
import time
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "latency" / "leadlag"))
import clob  # noqa: E402
import feeds  # noqa: E402
import load  # noqa: E402
import venues  # noqa: E402

OUT = ROOT / "data" / "cache" / "hidden" / "prep"


def _one(p_glob: str):
    return next(iter(load.LIVE.glob(p_glob)), None)


def do_hour(h: int) -> str:
    out = OUT / f"{h}.pkl"
    if out.exists():
        return f"{h} cached"
    t0 = time.time()
    mk = load.markets()
    up_of = dict(zip(mk[mk["fam"] == "5m"]["condition_id"], mk[mk["fam"] == "5m"]["up"]))
    res: dict[str, pd.DataFrame] = {}
    p = _one(f"*/clob_5m-{h}.tsv.gz")
    if p is not None:
        res.update(clob.parse(p, up_of))
    p = _one(f"*/binance-{h}.tsv.gz")
    if p is not None:
        d = feeds.binance(p, None)
        res["spot_tr"], res["spot_bk"] = d["trades"], d["book"]
    p = _one(f"*/binance_fut-{h}.tsv.gz")
    if p is not None:
        d = feeds.binance(p, "T")
        res["perp_tr"], res["perp_bk"] = d["trades"], d["book"]
    p = _one(f"*/chainlink-{h}.tsv.gz")
    if p is not None:
        res["chain"] = feeds.chainlink(p)
    for v in ("perp", "coinbase", "okx", "bybit"):
        p = next(iter((ROOT / "data" / "cache" / "hidden" / "venues").glob(f"*/{v}-{h}.tsv.gz")), None)
        if p is None:
            continue
        parsed = venues.parse(v, p)
        if v == "perp":  # keep the main recorder's perp book; take only the trades it lacks
            res["perp_tr"], res["vperp_bk"] = parsed["perp_tr"], parsed["perp_bk"]
        else:
            res.update(parsed)
    OUT.mkdir(parents=True, exist_ok=True)
    pd.to_pickle(res, out)
    return f"{h} done in {time.time() - t0:.0f} s: " + ", ".join(f"{k} {len(v)}" for k, v in res.items())


def main(hours: list[int]) -> None:
    if not hours:
        hs = sorted({int(p.name.split("-")[-1].split(".")[0]) for p in load.LIVE.glob("*/clob_5m-*.tsv.gz")})
        hours = [h for h in hs if (h + 1) * 3600 < time.time() + 12 - 60]
    with Pool(2) as pool:
        for msg in pool.imap_unordered(do_hour, hours):
            print(msg, flush=True)


if __name__ == "__main__":
    main([int(h) for h in sys.argv[1:]])
