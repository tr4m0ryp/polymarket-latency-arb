"""FROZEN 2026-10-11 ~15:35 UTC (data/out/predict/freeze.json) before any run-3 test hour
was simulated. Primary arm, family picks (sel1 rule: highest 10 s-markout $/day at L = 0
with positive markout and >= 100 fills/day), second-look variants (sel2, labelled), and the
baselines."""
from .base import ARMS as BASE
from .sel1 import ARMS as S1
from .sel2 import ARMS as S2

PRIMARY = "vt_v3p_m0.02_any"
PICKS = ("vt_v1_m0.02_trigger", "vt_v1_m0.01_micf", "vt_v1_m0.03_any", "vm_fair0.03_p-0.03")
SECOND = ("vt_v3p_m0.02_r0.1_s60_sl0.02", "vt_v3p_m0.02_r0.2_s150_sl0.02", "vm_v3p_fair0.02_p-0.03")

ARMS = list(BASE) + [a for a in S1 if a["name"] in (PRIMARY,) + PICKS] + [a for a in S2 if a["name"] in SECOND]
