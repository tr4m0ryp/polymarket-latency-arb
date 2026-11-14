"""Report of a live-test run (probe and / or micro), written to data/trade/<run>/report.md.

    python3 -m btclat.trade.report --run <run> [--no-gamma]

Micro: live fills vs the paper prediction for the same signals (fill rate, slippage, ack
latency, realised 10 s markout c/$ with a market-bootstrap CI, trades needed for the CI to
exclude 0). Probe: signing, POST / cancel round trips warm vs idle, error kinds, POP.
Hold test: ack by order type, marketable vs control; duplicate send: copies deduplicated?
Maker: quoting, fills/h, 10 s and resolution markouts, adverse selection, ack round trips,
real vs inferred fills, vs the simulator (report/maker/)."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from . import hold, load, micro, probe
from .maker import section as maker

TRADE = Path(__file__).resolve().parents[3] / "data" / "trade"


def build(root: Path, gamma: bool = True) -> str:
    out = [f"# Live test {root.name}", ""]
    ev = load.events(root)
    pre = next((e for e in ev if e.get("kind") == "preflight"), None)
    end = [e for e in ev if e.get("kind") == "session_end"]
    if pre:
        out += [f"Preflight: geoblock {pre.get('geoblock')}, balance ${pre.get('balance', 0):.2f}, "
                f"venue {pre.get('venue')}", ""]
    if end:
        out += [f"Session end: {end[-1].get('reason')}; cancel-all ok {end[-1].get('cancel_all_ok')}", ""]
    df = load.orders(root, gamma=gamma)
    if len(df):
        out += ["## Micro", "", *micro.section(df), ""]
    pr = load.probe(root)
    if len(pr):
        out += ["## Probe", "", *probe.section(pr), ""]
    ho, du = pd.DataFrame(load.rows(root, "hold")), pd.DataFrame(load.rows(root, "dup"))
    if len(ho):
        out += ["## Hold test", "", *hold.section(ho), ""]
    if len(du):
        out += ["## Duplicate send", "", *hold.dup_section(du), ""]
    mk = bool(load.rows(root, "quotes"))
    if mk:
        out += ["## Maker", "", *maker.section(root, gamma), ""]
    if not len(df) and not len(pr) and not len(ho) and not len(du) and not mk:
        out.append("(no orders or probe cycles logged)")
    return "\n".join(out) + "\n"


def main(argv=None, root: Path = TRADE) -> str:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--no-gamma", action="store_true", help="outcomes from the run's settle stream only")
    a = ap.parse_args(argv)
    d = root / a.run
    text = build(d, gamma=not a.no_gamma)
    (d / "report.md").write_text(text)
    print(text)
    return text


if __name__ == "__main__":
    main()
