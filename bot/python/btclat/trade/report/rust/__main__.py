"""Report of a Rust bot run, written to data/trade/<run>/report.md.

    python3 -m btclat.trade.report.rust --run <run> [--root data/trade]

Reads every bot-*.jsonl[.gz] of the run dir (see load.py), joins them per order (orders.py), and
reuses the micro report's fills / latency / markout tables (btclat.trade.report.micro), plus the
hold table (hold.py), signals / vetoes / skips by reason, errors and ack latency per copy."""
from __future__ import annotations

import argparse
from pathlib import Path


from btclat.trade.report import micro
from research.predict.report.md import md

from . import hold, load, orders, sections

TRADE = Path(__file__).resolve().parents[4] / "data" / "trade"


def build(run_dir: Path) -> str:
    fr = load.frames(run_dir)
    if not fr:
        return f"# Rust bot run {run_dir.name}\n\n(no bot-*.jsonl[.gz] events found in {run_dir})\n"
    df = orders.build(fr)
    out = sections.header(fr, run_dir.name) + ["## Signals", "", *sections.signals(fr)]
    if len(df):
        out += ["## Orders (micro view)", "",
                "Live-only run: paper columns are empty. Outcome from the `settle` stream; an unsettled fill is "
                "marked at its 10 s mid only.", "", *micro.section(df), ""]
        t = hold.table(df)
        if len(t):
            show = t[[c for c in hold.COLS]]
            out += ["## Hold", "", "Per order, send -> match -> ack (cents; depth = shares offered at <= limit):", "",
                    md(show, 3), "Summary by i:", "", md(hold.summary(t, "i"), 2), "Summary by i_mode:", "",
                    md(hold.summary(t, "i_mode"), 2)]
    out += ["## Errors", "", *sections.errors(fr, df), "## Latency", "", *sections.latency(fr, df)]
    return "\n".join(out) + "\n"


def main(argv=None, root: Path = TRADE) -> str:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--root", type=Path, default=root)
    a = ap.parse_args(argv)
    d = a.root / a.run
    text = build(d)
    d.mkdir(parents=True, exist_ok=True)
    (d / "report.md").write_text(text)
    print(text)
    return text


if __name__ == "__main__":
    main()
