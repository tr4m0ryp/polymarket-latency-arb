"""Cancel-tail check for the value makers (2026-10-13): live cancels ack in ~45 ms p50 but
113-149 ms p90, beyond the L = 50 rows. Run at --L 100,150 --hold 0.27 with the L = 50 model
(no models exist above 50 ms; a stale decision is exactly what a slow cancel costs)."""
from .hold import ARMS as H

PICK = ("vm_v1_fair0.03_p-0.02", "vm_v1_fair0.04_p-0.02", "vm_v1_fair0.03_p-0.03",
        "vm_v1_fair0.03_p-0.05", "vm_v1_fair0.04_p-0.05", "vm_v3p_fair0.04_p-0.04",
        "vm_v3p_fair0.04_p-0.03", "vm_fair0.05_p-0.03")
ARMS = [dict(a, model=f"{a['model']}_L50", per_L=False) for a in H if a["name"] in PICK]
assert len(ARMS) == len(PICK)
