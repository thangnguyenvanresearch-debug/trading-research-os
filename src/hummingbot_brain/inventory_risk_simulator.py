from __future__ import annotations


def inventory_risk(base_position: float, target_position: float, max_deviation: float) -> dict:
    deviation = abs(base_position - target_position)
    return {"deviation": deviation, "risk": "high" if deviation > max_deviation else "normal"}

