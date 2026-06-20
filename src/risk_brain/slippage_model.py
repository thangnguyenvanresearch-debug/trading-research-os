from __future__ import annotations


def estimate_slippage(spread_proxy: float, liquidity_score: float = 1.0) -> float:
    liquidity_penalty = 0.002 / max(liquidity_score, 0.1)
    return max(0.0, spread_proxy / 2 + liquidity_penalty)

