from __future__ import annotations

from core.models import Signal


def signal_from_status(status: str, score: int) -> Signal:
    if status in {"rejected", "archived"}:
        return Signal.AVOID
    if score >= 70:
        return Signal.LONG_CANDIDATE
    if score >= 45:
        return Signal.WAIT
    return Signal.AVOID
