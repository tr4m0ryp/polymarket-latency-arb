"""Score the live fused trigger's confirmation modes (fused.py) on a feed-race run.

    python3 recorder/feedrace/analysis/confirm.py data/cache/feedrace/<label> [HH:MM-HH:MM]

Per config at $5 and $10: fires, hit_1s (side ask reprices +1 c within 1 s of the fire: the
false-fire measure), and on the market-wide moves with a PM reprice within 2 s (pmresp.per_move)
the share of moves the config fires on, the share it fires before the reprice and the median
lead. A config's fire belongs to a move when it has the move's direction and lies in
[t0, t0 + 1 s] (t0 = first venue onset). Writes data/out/feedrace/confirm-<label>[-win].json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from fused import fires  # noqa: E402
from ids import q  # noqa: E402
from moves import WIN_NS, market_moves  # noqa: E402
from parse import lines  # noqa: E402
from pmresp import HIT_NS, Book  # noqa: E402
from run import mono_window  # noqa: E402
from signals import all_signals  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
PARTS = ("bn_spot_book", "bn_spot_trade", "bn_perp_book", "bn_perp_trade")


def deribit_quotes(run: Path) -> tuple[np.ndarray, ...]:
    """(mono, mid, bid amount, ask amount) of every quote, cached in parsed/deribit_q.npz."""
    dst = run / "parsed" / "deribit_q.npz"
    if not dst.exists():
        rows = []
        for f in sorted(run.glob("deribit-*.tsv.gz")):
            for ln in lines(f):
                parts = ln.split(b"\t", 2)
                if len(parts) < 3 or b'"quote.' not in parts[2]:
                    continue
                try:
                    d = json.loads(parts[2])["params"]["data"]
                    rows.append((int(parts[0]), (d["best_bid_price"] + d["best_ask_price"]) / 2,
                                 float(d["best_bid_amount"]), float(d["best_ask_amount"])))
                except (ValueError, KeyError, TypeError):
                    continue
        a = np.array(rows, dtype=object)
        np.savez(dst, mono=a[:, 0].astype(np.int64), px=a[:, 1].astype(float),
                 bq=a[:, 2].astype(float), aq=a[:, 3].astype(float))
    z = np.load(dst)
    o = np.argsort(z["mono"], kind="stable")
    t, p, bq, aq = z["mono"][o], z["px"][o], z["bq"][o], z["aq"][o]
    ok = np.isfinite(p) & (p > 0)
    return t[ok], p[ok], bq[ok], aq[ok]


def score(book: Book, moves: list[dict], venue: list[str], fl: list[tuple[int, int, str]]) -> dict:
    res = [book.reprice(t, s) for t, s, _ in fl]
    dl = [r for r, ok in res if ok]
    ft = {s: np.array([t for t, d, _ in fl if d == s], np.int64) for s in (1, -1)}
    lead, n, hit_m = [], 0, 0
    for m in moves:
        t0 = min(m["on"][v] for v in venue if v in m["on"])
        r, ok = book.reprice(t0, m["dir"])
        if not ok or r is None or r > 2 * HIT_NS:
            continue
        n += 1
        a = ft[m["dir"]]
        i = np.searchsorted(a, t0, side="left")
        if i < len(a) and a[i] <= t0 + WIN_NS:
            hit_m += 1
            lead.append((t0 + r - a[i]) / 1e6)
    src: dict[str, list] = {}
    for (*_, s), (r, ok) in zip(fl, res):
        c = src.setdefault(s, [0, 0, 0])
        c[0] += 1
        if ok:
            c[1] += 1
            c[2] += r is not None and r <= HIT_NS
    src = {k: {"n": v[0], "hit_1s": round(v[2] / v[1], 3) if v[1] else None} for k, v in src.items()}
    return {"fires": len(fl), "src": src, "hit_1s": round(float(np.mean([r is not None and r <= HIT_NS for r in dl])), 3)
            if dl else None, "moves": n, "fired_on_move": round(hit_m / max(1, n), 3),
            "before_pm_of_moves": round(sum(v > 0 for v in lead) / max(1, n), 3),
            "lead_ms": q(lead, (25, 50, 75))}


CONFIGS = [("binance_only", None, {}), ("binance_only_win0", None, {"win_ms": 0}), ("none", "none", {})] + \
    [(f"none_win{w:g}", "none", {"win_ms": w}) for w in (0, 100, 250, 500)] + \
    [(f"size_{s:g}", "size", {"size_ref": s}) for s in (5e3, 2e4, 5e4)] + \
    [(f"perp_w{w:g}_a0", "perp", {"w_ms": w, "agree": 0}) for w in (25, 50, 100)] + \
    [("perp_w50_a1", "perp", {"w_ms": 50, "agree": 1})] + \
    [(f"perp_w50_a0_win{w:g}", "perp", {"w_ms": 50, "agree": 0, "win_ms": w}) for w in (0, 250)] + \
    [(f"perp_w{w:g}_a0_win0", "perp", {"w_ms": w, "agree": 0, "win_ms": 0}) for w in (100, 200)] + \
    [("both_2e4_w50_a0", "both", {"size_ref": 2e4, "w_ms": 50, "agree": 0})]


def main(run: Path, spec: str | None = None) -> None:
    win = mono_window(run, spec)
    sigs = all_signals(run, win)
    book = Book(run)
    der = deribit_quotes(run)
    if win:
        m = (der[0] >= win[0]) & (der[0] < win[1])
        der = tuple(x[m] for x in der)
    assert np.array_equal(der[1], sigs["deribit_book"][1]), "deribit mids differ from signals.build"
    parts = {n: sigs[n] for n in PARTS}
    out = {"run": run.name, "window_utc": spec}
    for x in (5.0, 10.0):
        mv, venue = market_moves(sigs, x)
        r = {}
        for name, mode, kw in CONFIGS:
            fl = fires(parts, None if mode is None else der, x, mode or "none", **kw)
            r[name] = score(book, mv, venue, fl)
            print(f"${x:g} {name}: {json.dumps(r[name])}", flush=True)
        out[f"{x:g}"] = r
    tag = "-" + spec.replace(":", "").replace("-", "_") if spec else ""
    dst = ROOT / "data/out/feedrace" / f"confirm-{run.name}{tag}.json"
    dst.write_text(json.dumps(out, indent=1, default=float))
    print("wrote", dst)


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve(), sys.argv[2] if len(sys.argv) > 2 else None)
