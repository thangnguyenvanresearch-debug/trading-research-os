from __future__ import annotations


def exposure_allowed(pair_exposure: float, max_pair_exposure: float) -> bool:
    return pair_exposure <= max_pair_exposure

