"""Books-agree filter (post-hoc family): the hidden-trigger study (which saw all 24 h, so this
family is informed by the held-out hours) found the leaders' fills lose when the perp and spot
books disagree or point against them, and earn +1.3 c/$ when both books agree. Here the
baseline trigger and micf are restricted to moments when both microprices moved the same way.
Selected on training markets only, like every other family."""
from itertools import product

ARMS = [{"name": "theirs_micro_agree", "kind": "micro", "needs": "perp",
         "params": dict(win=0.1, thr=0.002, refr=0.2, band=(0.01, 0.99), tleft=30.0, fav_max=0.9,
                        shares=60.0, slip=0.02, agree=True)}]
for margin, thr, win, sh in product((0.0, 0.01, 0.02), (0.002, 0.01), (0.05, 0.1), (60.0, 150.0)):
    ARMS.append({"name": f"micfa_m{margin:g}_t{thr:g}_w{win:g}_s{sh:g}", "kind": "micro", "needs": "perp",
                 "params": dict(model="pzm", margin=margin, win=win, thr=thr, refr=0.2,
                                band=(0.05, 0.95), tleft=20.0, fav_max=0.97, shares=sh, slip=0.02,
                                agree=True)})
