"""Candidate C3: identity-projected firing score (two-side coherence instead of independent
side values). score.py = the identity and projections, cost.py = the match-time cost anchor,
arms.py = harness families (rounds 1-5), split.py = promoted / dropped order diagnostic,
run.py = harness runner with per-variant tables, diag_e.py / diag_ols.py = mechanism checks,
summarize.py = the result tables (data/out/predict/improve/c3_coherence/summary.md)."""
from .arms import (anti_taker, anti_veto, cm_taker, cm_veto, coh_taker, coh_veto, filt_taker, filt_veto,  # noqa: F401
                   lam_taker, lam_veto)
from .score import costs, projected, resid  # noqa: F401
