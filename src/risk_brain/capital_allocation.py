from __future__ import annotations


def capped_allocation(score: float, max_pair_exposure: float = 0.25) -> float:
    return round(max_pair_exposure * max(0.0, min(score, 100.0)) / 100, 4)

