from __future__ import annotations


def opportunity_score(gross_spread: float, fees: float, slippage: float) -> dict:
    net = gross_spread - fees - slippage
    return {"net_spread": net, "status": "ALERT" if net > 0 else "IGNORE", "auto_execution": False}

