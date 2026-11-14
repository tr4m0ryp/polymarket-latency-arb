"""Feed-race recorder: every stream in streams.STREAMS on one box, stamped on receipt.

    python3 record.py --hours 2 --out ~/feedrace/data/<label>

Each message gets CLOCK_MONOTONIC ns (comparable across processes on the box) and wall-clock ns
(chrony-disciplined; `chrony.tsv` logs the offset every 30 s). One process per stream group.
events-<group>.jsonl logs connects (remote ip, handshake ms), errors and skips. Read-only."""
from __future__ import annotations

import argparse
import asyncio
import json
import multiprocessing as mp
import os
import socket
import subprocess
import time
from pathlib import Path

import websockets

from sink import Sink
from streams import STREAMS, Stream


def _log(fh, **kw) -> None:
    fh.write(json.dumps({"mono": time.monotonic_ns(), "wall": time.time_ns(), **kw}) + "\n")
    fh.flush()


async def _pinger(ws, payload: str, every: float) -> None:
    while True:
        await asyncio.sleep(every)
        await ws.send(payload)


async def pump(name: str, s: Stream, sink: Sink, until: float, ev) -> None:
    hdr = {}
    if s.key_env:
        key = os.environ.get(s.key_env)
        if not key:  # probe once so the report can quote the venue's refusal, then skip
            try:
                async with websockets.connect(s.url, open_timeout=10):
                    _log(ev, kind="skip", feed=name, why="no key, yet connected")
            except Exception as e:
                _log(ev, kind="skip", feed=name, why=f"no {s.key_env}", probe=repr(e)[:300])
            return
        hdr = {"X-MBX-APIKEY": key}
    backoff = 1.0
    while time.time() < until:
        task = None
        try:
            t0 = time.monotonic_ns()
            async with websockets.connect(s.url, additional_headers=hdr, max_size=2**24,
                                          max_queue=None, compression=None, open_timeout=15,
                                          ping_interval=s.ws_ping, ping_timeout=20) as ws:
                sock = ws.transport.get_extra_info("socket")
                if sock is not None:
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                _log(ev, kind="connect", feed=name, ip=str(ws.remote_address[0]),
                     handshake_ms=(time.monotonic_ns() - t0) / 1e6)
                for h in ([s.hello] if isinstance(s.hello, str) else s.hello or ()):
                    await ws.send(h)
                if s.ping:
                    task = asyncio.create_task(_pinger(ws, s.ping, s.every))
                backoff = 1.0
                async for msg in ws:
                    sink.add(time.monotonic_ns(), time.time_ns(), msg)
                    if time.time() >= until:
                        break
        except Exception as e:  # log, back off, reconnect
            _log(ev, kind="error", feed=name, err=repr(e)[:300])
            await asyncio.sleep(backoff)
            backoff = min(30.0, backoff * 2)
        finally:
            if task:
                task.cancel()


async def _flusher(sinks: list[Sink], until: float) -> None:
    while time.time() < until + 2:
        await asyncio.sleep(0.5)
        for k in sinks:
            k.flush()


def run_group(group: str, out: str, until: float) -> None:
    root = Path(out)
    if group == "pm":
        return run_pm(root, until)
    names = [n for n, s in STREAMS.items() if s.group == group]
    sinks = {n: Sink(root, n) for n in names}
    with open(root / f"events-{group}.jsonl", "a") as ev:
        async def go():
            fl = asyncio.create_task(_flusher(list(sinks.values()), until))
            await asyncio.gather(*(pump(n, STREAMS[n], sinks[n], until, ev) for n in names))
            await fl
        asyncio.run(go())
    for k in sinks.values():
        k.flush()
        k.close()


def run_pm(root: Path, until: float) -> None:
    import pm
    sink = Sink(root, "pm")
    with open(root / "events-pm.jsonl", "a") as ev:
        async def go():
            fl = asyncio.create_task(_flusher([sink], until))
            await pm.run(sink, lambda **kw: _log(ev, **kw), until)
            await fl
        asyncio.run(go())
    sink.flush()
    sink.close()


def chrony_loop(out: Path, until: float) -> None:
    with open(out / "chrony.tsv", "a") as fh:
        while time.time() < until:
            try:
                r = subprocess.run(["chronyc", "-c", "tracking"], capture_output=True, text=True,
                                   timeout=5).stdout.strip()
            except Exception as e:
                r = "err " + repr(e)
            fh.write(f"{time.monotonic_ns()}\t{time.time_ns()}\t{r}\n")
            fh.flush()
            time.sleep(30)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=2.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--groups", default="", help="comma list; default all (adds to a live run)")
    a = ap.parse_args()
    out = Path(a.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    until = time.time() + a.hours * 3600
    groups = a.groups.split(",") if a.groups else sorted({s.group for s in STREAMS.values()}) + ["pm"]
    meta = {"host": socket.gethostname(), "start_wall_ns": time.time_ns(), "hours": a.hours,
            "streams": {n: s.url for n, s in STREAMS.items() if s.group in groups}}
    (out / f"meta{'-' + '-'.join(groups) if a.groups else ''}.json").write_text(json.dumps(meta, indent=1))
    procs = [mp.Process(target=run_group, args=(g, str(out), until), name=g) for g in groups]
    for p in procs:
        p.start()
    chrony_loop(out, until)
    for p in procs:
        p.join()


if __name__ == "__main__":
    main()
