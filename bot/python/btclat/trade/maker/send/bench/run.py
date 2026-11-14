"""Micro benchmark of the order send path, local only: no venue, no keys, no orders.

    python3 -m btclat.trade.maker.send.bench.run [--n 60] [--k 3] [--rate 3500] [--us 150]
        [--server-ms 0] [--sign real|emulated] [--senders thread,proc]
    taskset -c 0,1 python3 -m ...      (the Dublin box has 2 vCPUs)

A stand-in venue runs on 127.0.0.1 in its own process (server.py). Each trial sends n inserts,
each followed by its cancel, with the event loop idle and then under feed-like load (load.py),
through the in-process pool (`thread`, ops/live.py) or the sender process (`proc`, send/).
Per op: `loop` = from the manager's call to its callback running on the loop (what the bot
waits), `wire` = the sender thread's own round trip (t_send -> t_ack), `sign` (inserts).
loop - wire is the time our process adds around the request."""
from __future__ import annotations

import argparse
import asyncio
import multiprocessing as mp
import random
import time
from types import SimpleNamespace

import numpy as np

from ...ops.live import LiveOps
from ..remote import RemoteOps
from . import server
from .load import Load
from .venue import bench_venue

FACTORY = "btclat.trade.maker.send.bench.venue:bench_venue"


async def _op(loop, ops, kind: str, o) -> tuple[float, dict]:
    fut = loop.create_future()
    t0 = time.perf_counter()
    getattr(ops, kind)(o, lambda res: fut.done() or fut.set_result((time.perf_counter(), res)))
    t1, res = await fut
    return (t1 - t0) * 1e3, res


async def trial(sender: str, rate: float, a, host: str) -> list[dict]:
    loop = asyncio.get_running_loop()
    spec = {"factory": FACTORY, "host": host, "k": a.k, "sign": a.sign, "offset_ns": 0}
    v, h = bench_venue(spec, time.time_ns)
    ops = (LiveOps(v, h, loop.call_soon_threadsafe) if sender == "thread"
           else RemoteOps(v, h, loop.call_soon_threadsafe, lambda kind, **kw: None, loop, spec, mode="proc"))
    await asyncio.to_thread(h.warm, 0.0)
    stop, load = asyncio.Event(), Load(rate, a.us)
    task = asyncio.create_task(load.run(stop))
    await asyncio.sleep(0.5)
    rows, rng, c0 = [], random.Random(1), time.process_time()
    for i in range(a.n):
        o = SimpleNamespace(cid=f"b{i}", token="1234", price=0.33, size=5.0, otype="GTD",
                            expiration=int(time.time()) + 200, oid=None)
        for kind in ("insert", "cancel"):
            ms, res = await _op(loop, ops, kind, o)
            o.oid = o.oid or res.get("order_id")
            rows.append({"sender": sender, "rate": rate, "op": kind, "loop": ms, "wire": res.get("ms", np.nan),
                         "sign": res.get("sign_us", np.nan) / 1e3, "ok": bool(res.get("ok") or res.get("confirmed"))})
            await asyncio.sleep(0.02)
        await asyncio.sleep(0.05 + 0.05 * rng.random())
    cpu = time.process_time() - c0
    stop.set()
    await task
    if hasattr(ops, "detach"):
        ops.detach()
    await asyncio.to_thread(ops.close)
    span = sum(r["loop"] for r in rows) / 1e3 + a.n * 0.115
    for r in rows:
        r["msgs_s"], r["cpu"] = load.n / max(span, 1e-9), cpu / max(span, 1e-9)
    return rows


def _q(x, p):
    x = np.asarray([v for v in x if v == v])
    return float(np.quantile(x, p)) if len(x) else float("nan")


def main(argv=None) -> list[dict]:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--rate", type=float, default=3500.0)
    ap.add_argument("--us", type=float, default=150.0, help="Python work per feed message (us)")
    ap.add_argument("--server-ms", type=float, default=0.0)
    ap.add_argument("--sign", default="real", choices=("real", "emulated"))
    ap.add_argument("--senders", default="thread,proc")
    a = ap.parse_args(argv)
    ctx = mp.get_context("spawn")
    q = ctx.Queue()
    srv = ctx.Process(target=server.serve, args=(q, a.server_ms), daemon=True)
    srv.start()
    host = f"http://127.0.0.1:{q.get(timeout=20)}"
    rows = []
    try:
        for rate in (0.0, a.rate):
            for sender in a.senders.split(","):
                rows += asyncio.run(trial(sender, rate, a, host))
    finally:
        srv.kill()
    print(f"{'sender':7s} {'load':>9s} {'op':7s} {'n':>3s} {'loop p50':>9s} {'p90':>7s} {'p99':>7s} "
          f"{'wire p50':>9s} {'p90':>7s} {'added p50':>10s} {'p90':>7s} {'sign p50':>9s} {'cpu':>5s}")
    for (sender, rate, op) in dict.fromkeys((r["sender"], r["rate"], r["op"]) for r in rows):
        g = [r for r in rows if (r["sender"], r["rate"], r["op"]) == (sender, rate, op)]
        add = [r["loop"] - r["wire"] for r in g]
        print(f"{sender:7s} {g[0]['msgs_s']:7.0f}/s {op:7s} {len(g):3d} {_q([r['loop'] for r in g], .5):9.2f} "
              f"{_q([r['loop'] for r in g], .9):7.2f} {_q([r['loop'] for r in g], .99):7.2f} "
              f"{_q([r['wire'] for r in g], .5):9.2f} {_q([r['wire'] for r in g], .9):7.2f} {_q(add, .5):10.2f} "
              f"{_q(add, .9):7.2f} {_q([r['sign'] for r in g], .5):9.2f} {g[0]['cpu']:5.2f}")
    bad = [r for r in rows if not r["ok"]]
    if bad:
        print(f"{len(bad)} ops not ok")
    return rows


if __name__ == "__main__":
    main()
