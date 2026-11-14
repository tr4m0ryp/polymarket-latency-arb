"""Mechanism-derived drop rules read window by window (thresholds are round numbers chosen
after looking at all allowed windows: diagnostics, not selections). Signature fn(window
fills, all fills of that arm x L) -> drop mask."""
RULES = {
    "delta < 3 c/bp": lambda x, g: x["delta"] < 3,
    "delta < 5 c/bp": lambda x, g: x["delta"] < 5,
    "rv60 > 4 bp": lambda x, g: x["rv60"] > 4,
    "pm_stale <= 0": lambda x, g: x["pm_stale"] <= 0,
    "seen > 0.80": lambda x, g: x["seen"] > 0.80,
    "pred_gap < select q20": lambda x, g: x["pred_gap"] < g.loc[g["window"] == "select", "pred_gap"].quantile(0.2),
}
DELTA_GRID = (2.0, 3.0, 4.0, 5.0, 6.0, 8.0)
