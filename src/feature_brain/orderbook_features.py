from __future__ import annotations


def fee_adjusted_spread(bid: float, ask: float, taker_fee: float = 0.001) -> float:
    if bid <= 0 or ask <= 0:
        return 0.0
    gross = (ask - bid) / ((ask + bid) / 2)
    return gross - 2 * taker_fee

