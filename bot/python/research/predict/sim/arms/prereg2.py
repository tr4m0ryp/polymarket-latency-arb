"""Arms of data/out/predict/prereg2.json (registered 2026-10-11 22:15 UTC): the two primary
arms exactly as frozen in final.py, plus the micf and theirs_micro baselines. Nothing tuned."""
from .base import ARMS as BASE
from .sel1 import ARMS as S1

PRIMARY = ("vt_v1_m0.03_any", "vt_v1_m0.02_trigger")

ARMS = list(BASE) + [a for a in S1 if a["name"] in PRIMARY]
assert {a["name"] for a in ARMS} == {"theirs_micro", "micf", *PRIMARY}
