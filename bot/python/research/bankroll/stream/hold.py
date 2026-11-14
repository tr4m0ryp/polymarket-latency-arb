"""Hold distributions (decision -> venue match, seconds).

`old`: the 195 live FAK orders of 2026-10-13 (research/vetohold hold.json, ack - 14 ms).
`new`: the 25 orders of the Rust bot run dublin-bot-20261014b. Each order went out as k = 3
identical copies; the copies the venue rejects before matching (duplicate / balance) answer in
~50 ms, the one copy that reaches the matching engine answers after the hold. The match is that
engine answer (fak_no_match or matched) - 14 ms, measured from the decision.
`fast50`: a fixed 50 ms what-if (what the first-ack figure would imply; refuted, see report)."""
from __future__ import annotations

import gzip
import json
from collections import defaultdict

import numpy as np

from research.vetohold import OUT as VOUT, ROOT

BOT_RUN = ROOT / "data" / "trade" / "dublin-bot-20261014b"
ACK_AFTER_MATCH = 0.014
PRE_ENGINE = ("balance", "duplicate")


def bot_run_acks(run=BOT_RUN) -> dict:
    """Per order: first ack of any copy, engine ack, decision -> match (all seconds)."""
    orders, acks = {}, defaultdict(list)
    for f in sorted(run.glob("bot-*.jsonl.gz")):
        with gzip.open(f, "rt") as fh:
            for line in fh:
                if '"kind":"order"' not in line and '"kind":"ack"' not in line:
                    continue
                d = json.loads(line)
                (orders.__setitem__(d["cid"], d) if d["kind"] == "order" else acks[d["cid"]].append(d))
    out = {}
    for cid, o in orders.items():
        a = acks.get(cid, [])
        eng = [x for x in a if x.get("err_kind") not in PRE_ENGINE]
        if not a or not eng:
            continue
        e = min(eng, key=lambda x: x["latency_ns"])
        out[cid] = {"first_ack": min(x["latency_ns"] for x in a) / 1e9, "engine_ack": e["latency_ns"] / 1e9,
                    "pre_engine": [x["latency_ns"] / 1e9 for x in a if x.get("err_kind") in PRE_ENGINE],
                    "hold": (e["t_ack_mono_ns"] - o["t_dec_mono_ns"]) / 1e9 - ACK_AFTER_MATCH}
    return out


def holds() -> dict:
    old = np.sort(np.array(json.loads((VOUT / "hold.json").read_text())["ms"]) / 1e3)
    new = np.sort(np.array([v["hold"] for v in bot_run_acks().values()]))
    return {"old": old, "new": new, "fast50": np.array([0.050])}
