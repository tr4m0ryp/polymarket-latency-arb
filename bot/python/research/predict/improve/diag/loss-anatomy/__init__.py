"""Loss anatomy of the deployed predictive arms (post-freeze diagnostic, no arm changes).

Question: which state, observable at decision time, separates the losing fills and the worst
markets of vt_v1_m0.03_any and vt_v1_m0.02_trigger (micf for contrast) from the winners, at
L = 0 and -40, on every allowed window (select, dev3, test3 run 1, ext)? Edge = 10 s markout.

Sealed data: market lists come only from earlier frozen runs' markets-<tag>.csv, every list is
asserted to start before SEALED, and Polymarket events are read only from hour files that END
at or before SEALED (stricter than the frozen ext run: the 18:00 hour is never opened, so the
eleven 18:00-18:50 ext markets get no venue-depth columns).

The directory name has a hyphen, so it runs as a directory, registered as `loss_anatomy`:

    OMP_NUM_THREADS=2 nice -n 10 python3 research/predict/improve/diag/loss-anatomy build
    python3 research/predict/improve/diag/loss-anatomy analyze"""
from research.predict import CACHE as PCACHE, OUT as POUT  # noqa: F401
from research.strategy import CACHE as SCACHE  # noqa: F401

SEALED = 1791744900              # 2026-10-11 18:55 UTC: prereg2 test segment starts here
WINDOWS = {"select": "sel1", "dev3": "dev1", "test3r1": "final", "ext": "ext"}
UNSEEN = ("dev3", "test3r1", "ext")
ARMS = ("vt_v1_m0.03_any", "vt_v1_m0.02_trigger", "micf")
SHORT = {"vt_v1_m0.03_any": "taker1s", "vt_v1_m0.02_trigger": "veto", "micf": "micf"}
LS = (0, -40)
MODEL = "v1"                     # the deployed arms' 1 s value model, per L
OUT = POUT / "improve"
WORK = OUT / "loss-anatomy"
