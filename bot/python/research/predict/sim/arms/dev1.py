"""Run-3 dev hours: transfer check of the sel1 picks (one per family, rule in
reports/predict.md) against the baselines, before anything is frozen."""
from .base import ARMS as BASE
from .sel1 import ARMS as S1

PICKS = ("vt_v3p_m0.02_any", "vt_v1_m0.02_trigger", "vt_v1_m0.01_micf", "vm_fair0.03_p-0.03",
         "vm_book_p-0.03", "vt_v1_m0.03_any")
ARMS = list(BASE) + [a for a in S1 if a["name"] in PICKS]
