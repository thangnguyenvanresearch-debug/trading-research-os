from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResearchEvent:
    timestamp: str
    symbol: str
    event_type: str
    payload: dict

