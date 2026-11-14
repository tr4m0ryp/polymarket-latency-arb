"""Live feature state vs the offline pipeline on one recorded market (~2 min).

Rows where the offline table reads the Polymarket book one grid step early (see
btclat/paper/replay/compare.py) are excluded from the feature bound and reported apart."""
import numpy as np
import pytest

from btclat.paper.replay import parity, source
from btclat.paper.replay.compare import compare, grid_quirk
from btclat.paper.replay.scores import score_parity

HOUR = 497697


@pytest.mark.skipif(not list(source.LIVE.glob(f"*/clob_5m-{HOUR}.tsv.gz")), reason="recording not present")
def test_live_features_match_offline():
    tabs, _ = parity.offline(HOUR, 1)
    rows = parity.live_rows(HOUR, tabs)
    starts = {s: int(s.rsplit("-", 1)[1]) for s in tabs}
    df, counts = compare(tabs, rows, starts)
    clean = df[df["rows"] == "clean"]
    book = clean[clean["col"].str.match(r"^[ps]_")]
    assert book["max_z"].max() < 0.1, book.head()           # Binance book state: float noise only
    assert clean["frac_z_gt_1e-3"].max() < 0.01, clean.head()  # look-ahead columns: rare rows
    quirk = {s: grid_quirk(d["t"], starts[s]) for s, d in tabs.items()}
    sc = score_parity(tabs, rows, quirk=quirk)
    assert sc["vector_max_abs_c"] < 1e-9
    assert sc["live"]["clean"]["p99_abs_c"] < 0.1
    o = sc["orders"]["vt_v1_m0.02_trigger"]
    assert o["matched"] >= 0.8 * max(o["offline"], 1)
