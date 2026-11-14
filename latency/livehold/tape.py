"""Filter the paper box CLOB tape to the tokens and time windows of our live orders.

Keeps every message that names one of our tokens within [send - 120 s, send + 20 s] of one of
its orders (book snapshots, price_change, last_trade_price), as (recv_s, json) lines in
data/trade/tape/ours.tsv.gz. One pass over ~1.2 GB of gzip; grep does the token match."""
from __future__ import annotations

import gzip
import subprocess

import numpy as np

from . import TAPE
from .orders import load

PRE, POST = 120.0, 20.0


def main():
    o = load()
    toks = sorted(set(o["token"]))
    (TAPE / "tokens.txt").write_text("\n".join(toks) + "\n")
    win = {t: np.sort(o.loc[o["token"] == t, "t_send"].to_numpy()) for t in toks}
    hours = sorted({int(t // 3600) for t in o["t_send"]} | {int((t - PRE) // 3600) for t in o["t_send"]})
    n_in = n_out = 0
    with gzip.open(TAPE / "ours.tsv.gz", "wt") as out:
        for h in hours:
            src = TAPE / f"clob_5m-{h}.tsv.gz"
            if not src.exists():
                print("missing", src.name)
                continue
            p = subprocess.Popen(f"zcat {src} | grep -F -f {TAPE / 'tokens.txt'}", shell=True,
                                 stdout=subprocess.PIPE, text=True)
            for line in p.stdout:
                n_in += 1
                ts = int(line[:19]) / 1e9
                for t in toks:
                    if t in line:
                        s = win[t]
                        i = np.searchsorted(s, ts - POST)
                        if i < len(s) and s[i] <= ts + PRE:
                            out.write(line)
                            n_out += 1
                            break
            p.wait()
            print(h, n_in, n_out, flush=True)


if __name__ == "__main__":
    main()
