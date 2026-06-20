from __future__ import annotations


def quote_distance_simulation(mid_price: float, spread_bps: float) -> dict:
    distance = mid_price * spread_bps / 10000
    return {"bid": mid_price - distance, "ask": mid_price + distance, "paper_only": True}

