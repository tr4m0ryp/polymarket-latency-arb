"""A synthetic Rust bot run written straight as btl_log JSONL / JSONL.gz (no Rust needed).

Two orders (k = 2 copies each): r:0 fills 5 sh at 0.42 (fill reported twice, via post and
user_ws, same trade_id), r:1 misses (FAK no match). Also a vetoed signal, a risk skip, a book
snapshot set per order, and three file shapes: complete gz, plain with a truncated last line,
and a gzip cut without its trailer."""
import gzip
import json
import zlib

H = 490_000
NS = 1_000_000_000
T0 = H * 3600 + 10          # wall s of the first signal
RUN = "r"


class Seq:
    def __init__(self):
        self.n = 0
        self.rows = []

    def add(self, kind, wall, /, **f):
        self.rows.append({"run": RUN, "seq": self.n, "mono_ns": int(wall * NS) - 5 * 10**17, "wall_ns": int(wall * NS), "kind": kind, **f})
        self.n += 1


def book(s, cid, at, t, ba, depth, mid, up=True):
    s.add("book", t, cid=cid, at=at, slug="btc-updown-5m-1", t=t, up=up, bids=[[ba - 0.02, 50]], asks=[[ba, depth]],
          bb=ba - 0.02, ba=ba, mid=mid, depth_le_limit=depth)


def events():
    s = Seq()
    s.add("start", T0 - 5, mode="live", args={"size": 5}, model={"name": "vt_v1", "sha256": "ab", "sha16": "ab12", "n_trees": 300},
          limits={"max_orders_hour": 30}, i_mode="fixed", i=0.01, i_set=[0.01], host="h", version="0.1")
    s.add("market", T0 - 4, slug="btc-updown-5m-1", start=T0, end=T0 + 300, up="u", down="d", condition_id="c", tick=0.01)
    for n, (dec, reason) in enumerate([("order", None), ("order", None), ("veto", "margin"), ("skip", "max_orders_hour")]):
        t = T0 + 10 * n
        s.add("signal", t, sig=f"r:{n}", slug="btc-updown-5m-1", t=t, src="pb", vts=t - 0.11, pu=0.6, pdn=0.4, edge=0.05,
              side=1, seen=0.40, secs_left=200, decision=dec, reason=reason, feat_ns=2000, model_ns=30000, features={"x": 1.0, "y": None})
    s.add("skip", T0 + 30, sig="r:3", cid="r:3", reason="max_orders_hour")
    for n, (seen, lim, ba_send, ba_ack, d_send, d_ack, mid10) in enumerate([(0.40, 0.42, 0.41, 0.42, 100.0, 60.0, 0.50),
                                                                           (0.45, 0.46, 0.45, 0.48, 100.0, 0.0, 0.40)]):
        cid, t = f"r:{n}", T0 + 10 * n
        s.add("order", t + 0.001, sig=cid, cid=cid, slug="btc-updown-5m-1", token="tok", up=True, side=1, seen=seen, i=0.01,
              i_mode="fixed", limit=lim, size=5.0, order_type="FAK", k=2, dry=False, t=t + 0.001, t_dec_mono_ns=int(t * NS) + 10**6 - 5 * 10**17,
              build_ns=1000, sign_ns=1_400_000, maker_amount=2, taker_amount=5, salt=1, ts_ms=1)
        book(s, cid, "signal", t, ba_send, d_send, 0.40)
        for c in (0, 1):
            ts = t + 0.003 + 0.0001 * c
            s.add("send", ts, cid=cid, copy=c, conn=c, t_send_mono_ns=int(ts * NS) - 5 * 10**17, t_send_wall_ns=int(ts * NS))
        book(s, cid, "send", t + 0.003, ba_send, d_send, 0.40)
        for c, lat in ((0, 0.100), (1, 0.130)):
            ta = t + 0.003 + 0.0001 * c + lat
            filled = n == 0 and c == 0
            s.add("ack", ta, cid=cid, copy=c, conn=c, code=200, ok=c == 0, status="matched" if filled else "unmatched",
                  order_id=f"o{n}", latency_ns=int(lat * NS), t_ack_mono_ns=int(ta * NS) - 5 * 10**17, t_ack_wall_ns=int(ta * NS),
                  err_kind=None if c == 0 and filled else ("duplicate" if c else "fak_no_match"),
                  fill_sh=5.0 if filled else 0.0, fill_cost=2.1 if filled else 0.0, px=0.42 if filled else None, trade_ids=[])
        book(s, cid, "ack", t + 0.103, ba_ack, d_ack, 0.45)
        book(s, cid, "ack+10s", t + 10.1, 0.5, 50.0, mid10)
        if n == 0:
            for src, ft in (("post", 0.11), ("user_ws", 0.30)):
                s.add("fill", t + ft, cid=cid, order_id="o0", src=src, sh=5.0, px=0.42, cost=2.1, fee=None, trade_id="tr1",
                      match_t=t + 0.09, status="MATCHED")
    s.add("error", T0 + 40, where="feed:pm", err="reset")
    s.add("settle", T0 + 301, slug="btc-updown-5m-1", outcome=1.0)
    s.add("log_stats", T0 + 302, written=40, dropped=0, queued=0, io_errors=0)
    s.add("stop", T0 + 303, reason="sigterm", cancel_all_ok=True)
    return s.rows


def write_run(d):
    d.mkdir(parents=True, exist_ok=True)
    ev = events()
    a, b, c = ev[:8], ev[8:30], ev[30:]
    with gzip.open(d / f"bot-{H}.jsonl.gz", "wt") as fh:
        fh.writelines(json.dumps(e) + "\n" for e in a)
    # plain hour file, last line cut mid-write
    txt = "".join(json.dumps(e) + "\n" for e in b) + '{"run":"r","seq":999,"mono_ns":1,"wal'
    (d / f"bot-{H + 1}.jsonl").write_text(txt)
    # gzip cut without its trailer (sync-flushed so the lines before the cut are readable)
    z = zlib.compressobj(wbits=31)
    raw = z.compress(("".join(json.dumps(e) + "\n" for e in c)).encode()) + z.flush(zlib.Z_SYNC_FLUSH)
    (d / f"bot-{H + 2}.jsonl.gz").write_bytes(raw)
    return d
