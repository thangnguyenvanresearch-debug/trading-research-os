from __future__ import annotations


def apply_fee(return_value: float, fee_rate: float = 0.001, turns: int = 2) -> float:
    return return_value - fee_rate * turns

