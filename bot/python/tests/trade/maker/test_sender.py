"""The sender process (maker/send/): inserts and cancels signed and sent from a second process,
answers back on the event loop, every copy reported, A/B routing tagged, a dead sender fails
closed (every op `unknown`: the manager stops). Plus --far (0.01 inserts at the rule's
instants). Local only: a stand-in venue on 127.0.0.1 (send/bench/server.py), no keys."""
import asyncio
import multiprocessing as mp
import time
from types import SimpleNamespace

import pytest

from btclat.trade import __main__ as cli
from btclat.trade.maker.send import RemoteOps
from btclat.trade.maker.send.bench import server
from btclat.trade.maker.send.bench.venue import bench_venue

from .fakes import manager, q

FACTORY = "btclat.trade.maker.send.bench.venue:bench_venue"


@pytest.fixture(scope="module")
def host():
    ctx = mp.get_context("spawn")
    qq = ctx.Queue()
    p = ctx.Process(target=server.serve, args=(qq, 0.0), daemon=True)
    p.start()
    yield f"http://127.0.0.1:{qq.get(timeout=20)}"
    p.kill()


def _order(i=0):
    return SimpleNamespace(cid=f"m{i}", token="1234", price=0.33, size=5.0, otype="GTD",
                           expiration=int(time.time()) + 200, oid=None)


async def _call(ops, kind, o):
    fut = asyncio.get_running_loop().create_future()
    getattr(ops, kind)(o, lambda res: fut.done() or fut.set_result(res))
    return await asyncio.wait_for(fut, 10)


def _ops(loop, host, mode="proc", notes=None, seed=None):
    spec = {"factory": FACTORY, "host": host, "k": 2, "sign": "emulated", "offset_ns": 0}
    v, h = bench_venue(spec, time.time_ns)
    note = (lambda kind, **kw: notes.append((kind, kw))) if notes is not None else (lambda kind, **kw: None)
    return RemoteOps(v, h, loop.call_soon_threadsafe, note, loop, spec, mode=mode, seed=seed)


def test_proc_sender_round_trip(host):
    async def go():
        notes = []
        ops = _ops(asyncio.get_running_loop(), host, notes=notes)
        o = _order()
        res = await _call(ops, "insert", o)
        assert res["ok"] and res["via"] == "proc" and res["order_id"].startswith("0x") and res["k"] == 2
        assert res["t_ack_ns"] > res["t_send_ns"] and res["sign_us"] > 0
        o.oid = res["order_id"]
        res = await _call(ops, "cancel", o)
        assert res["confirmed"] and res["via"] == "proc" and res["gone"] is None
        for _ in range(100):
            if sum(k == "copies" for k, _ in notes) == 2:
                break
            await asyncio.sleep(0.02)
        cps = [kw for k, kw in notes if k == "copies"]
        assert [c["what"] for c in cps] == ["insert", "cancel"] and all(len(c["copies"]) == 2 for c in cps)
        ops.set_offset(5_000_000)
        ops.detach()
        await asyncio.to_thread(ops.close)
        assert not ops.proc.is_alive()
    asyncio.run(go())


def test_dead_sender_fails_closed(host):
    async def go():
        notes = []
        ops = _ops(asyncio.get_running_loop(), host, notes=notes)
        ops.proc.kill()
        ops.proc.join(5)
        for _ in range(100):
            if ops.dead:
                break
            await asyncio.sleep(0.02)
        res = await _call(ops, "insert", _order())
        assert res["unknown"] and not res["ok"] and "sender" in res["exc"]
        assert any(k == "sender_dead" for k, _ in notes)
        ops.detach()
        await asyncio.to_thread(ops.close)
    asyncio.run(go())


def test_ab_routes_ops_both_ways(host):
    async def go():
        ops = _ops(asyncio.get_running_loop(), host, mode="ab", seed=7)
        vias = [(await _call(ops, "insert", _order(i)))["via"] for i in range(12)]
        assert set(vias) == {"proc", "thread"} and ops.n_via["proc"] + ops.n_via["thread"] == 12
        ops.detach()
        await asyncio.to_thread(ops.close)
    asyncio.run(go())
    with pytest.raises(ValueError):
        RemoteOps(None, None, None, None, None, {}, mode="fork")


def test_far_inserts_at_one_cent_at_the_rule_instants(tmp_path):
    w = manager(tmp_path)
    w.mgr.far = True
    w.mgr.on_quote(w.m, q(w.clock.t, bid=47, ask=53))
    o_bid, o_ask = w.ops.ack("insert"), w.ops.ack("insert")
    assert (o_bid.tick, o_bid.price, o_ask.tick, o_ask.price) == (47, 0.01, 53, 0.01)
    assert w.mgr.resting() == pytest.approx(2 * 5 * 0.01)
    w.mgr.on_quote(w.m, q(w.clock.t + 0.1, bid=48, ask=53))       # the rule moves: cancel as live
    assert w.ops.n("cancel") == 1


def test_far_and_sender_refused_in_dry(tmp_path):
    for extra in (["--far"], ["--sender", "proc"]):
        with pytest.raises(SystemExit):
            cli.start(["maker", "--dry", "--run", "x", *extra], config=tmp_path, root=tmp_path / "runs")
