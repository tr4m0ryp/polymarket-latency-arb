"""README bounds: net dollars per 30 days at each fee-refund tier, all at the order flow
that would trade VOLUME if every order filled.

net(r) = sought volume x dollar fill rate x (gross edge - fee x (1 - r)) / 100, fee = 3.01 c
per dollar (p = 0.57) in every scenario so that only fills and edge differ."""
from __future__ import annotations

from .. import FEE_CPD, G_README, TIERS, VOLUME


def net(fill: float, edge_cpd: float) -> dict:
    return {f"{int(round(100 * r))}": float(round(VOLUME * fill * (edge_cpd - FEE_CPD * (1 - r)) / 100, 0))
            for r in TIERS}


def scenario(name: str, fill: float, edge: float, source: str) -> dict:
    return {"name": name, "fill_rate_dollars": round(fill, 4), "gross_edge_cpd": round(edge, 3),
            "filled_volume_30d": round(VOLUME * fill, 0),
            "order_flow_multiple_for_full_volume": round(1 / fill, 2) if fill > 0 else None,
            "breakeven_refund": round(1 - edge / FEE_CPD, 3), "net_30d_by_tier_pct": net(fill, edge),
            "source": source}


def bounds(row165: dict, live_b: dict) -> dict:
    fr = row165["fill_rate_dollars"]["est"]
    ea, ef = row165["edge_all_cpd"]["est"], row165["edge_filled_cpd"]["est"]
    out = {"upper": scenario("every order fills", 1.0, G_README, "README: g = 2.44 c/$, all orders fill")}
    out["central_raw"] = scenario("replay d = 165 ms, raw", fr, ef,
                                  "replay: dollar fill rate and filled-order edge as measured")
    out["central_shifted"] = scenario(
        "replay d = 165 ms, shifted to g = 2.44", fr, G_README + (ef - ea),
        "replay fill rate; edge = 2.44 + (replay filled edge - replay all-order edge)")
    if ea > 0:   # the requested ratio rescale; unstable when the all-order edge's interval spans 0
        out["central_ratio"] = scenario(
            "replay d = 165 ms, ratio-scaled to g = 2.44", fr, G_README * ef / ea,
            "replay fill rate; edge = 2.44 x replay filled edge / replay all-order edge")
        lo, hi = row165["edge_all_cpd"]["lo"], row165["edge_all_cpd"]["hi"]
        out["central_ratio"]["defensible"] = bool(lo > 0)
        out["central_ratio"]["note"] = f"all-order edge {ea} [{lo}, {hi}] c/$: ratio undefined inside the interval"
    lf, lg = live_b["fill_rate_dollars"]["est"], live_b["gross_mk10_cpd"]["est"]
    out["lower"] = scenario("live micro run (Dublin, 4 h)", lf, lg,
                            "live run b: dollar fill rate and gross 10 s markout of the 22 fills")
    return out
