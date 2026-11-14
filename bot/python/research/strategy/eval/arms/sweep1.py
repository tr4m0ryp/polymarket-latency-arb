"""Sweep 1: the leaders' rule (baselines), its tuned family, and the fair-value taker.

theirs_spot: side = sign of the last 3 s spot move, fire on any move (the leaders fire about as
often on no-move seconds as on moves, reverse.md), at most every 2 s (their median gap ~3 s),
while favourite <= 0.90 and >= 30 s remain, 60 shares, marketable limit = seen ask + 1 tick.
At this setting it fires ~30 times per 5m market in training, between A (24) and B (39)."""
from itertools import product

THEIRS = dict(win=3.0, thr=1e-4, refr=2.0, band=(0.01, 0.99), tleft=30.0, fav_max=0.9,
              shares=60.0, slip=0.01)

ARMS = [
    {"name": "theirs_spot", "kind": "momentum", "params": dict(src="spot", **THEIRS), "keep": True},
    {"name": "theirs_perp", "kind": "momentum", "params": dict(src="perp", **THEIRS),
     "needs": "perp", "keep": True},
]

for src, win, thr, band, refr in product(("spot", "smid", "perp"), (0.2, 0.5, 1.0, 3.0),
                                         (0.3, 0.5, 1.0, 2.0), ((0.01, 0.99), (0.10, 0.70)),
                                         (0.5, 2.0)):
    ARMS.append({"name": f"mom_{src}_w{win:g}_t{thr:g}_b{band[1]:g}_r{refr:g}", "kind": "momentum",
                 "params": dict(src=src, win=win, thr=thr, refr=refr, band=band, tleft=30.0,
                                fav_max=0.9, shares=60.0, slip=0.01),
                 "needs": "perp" if src == "perp" else None})

for src, win, thr in product(("smid", "perp"), (0.2, 0.5, 1.0), (0.05, 0.1, 0.2, 0.4)):
    ARMS.append({"name": f"zmom_{src}_w{win:g}_z{thr:g}", "kind": "momentum",
                 "params": dict(src=src, win=win, thr=thr, refr=0.5, band=(0.05, 0.95),
                                tleft=20.0, fav_max=0.97, shares=60.0, slip=0.01, znorm=True),
                 "needs": "perp" if src == "perp" else None})

for model, margin, m_fill, refr in product(("pz", "pzx", "s"), (0.01, 0.02, 0.03, 0.05, 0.08),
                                           (0.0, 0.01, 0.02), (0.25, 1.0)):
    ARMS.append({"name": f"fair_{model}_m{margin:g}_f{m_fill:g}_r{refr:g}", "kind": "fair",
                 "params": dict(model=model, margin=margin, m_fill=m_fill, refr=refr),
                 "needs": None if model == "s" else "perp"})
