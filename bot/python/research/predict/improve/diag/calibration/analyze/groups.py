"""Feature groups of the value model (as model/importance.py), resolved to column indices."""
from __future__ import annotations

GROUPS = {"perp microprice change": ("p_dmic",), "perp queue / imbalance": ("p_imb", "p_micoff", "p_lq"),
          "perp OFI (CKS)": ("p_ofi",), "perp depletion / time-to-depletion": ("p_dep", "p_ttd"),
          "perp intensities / last tick": ("p_up", "p_dn", "p_lam", "p_tsm", "p_lastdir", "p_dmid", "p_spr"),
          "spot book": ("s_",), "spot trades": ("st_",), "perp-spot basis": ("basis_dev", "mic_dev"),
          "Polymarket state": ("tok_mid", "seen", "half_spread", "pm_", "bk", "secs_left"),
          "settlement scale (sigma, zs, delta)": ("lzs", "sigma", "delta"),
          "fair value (pzm, gap)": ("fair_", "gap"), "delta-scaled Binance": ("_c",)}


def group_cols(vf: list[str], g: str) -> list[int]:
    pre = GROUPS[g]
    if pre == ("_c",):
        return [i for i, c in enumerate(vf) if c.endswith("_c")]
    return [i for i, c in enumerate(vf) if c.startswith(pre) and not c.endswith("_c")]
