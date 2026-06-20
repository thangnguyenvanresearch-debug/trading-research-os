from __future__ import annotations


def out_of_sample_passed(metrics: dict, minimum: float = 0.0) -> bool:
    try:
        return float(metrics.get("out_of_sample_return", 0.0) or 0.0) >= minimum
    except (TypeError, ValueError):
        return False
