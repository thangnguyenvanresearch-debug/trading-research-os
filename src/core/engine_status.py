from __future__ import annotations

from typing import Literal, TypedDict


EngineStatusValue = Literal["missing", "installed", "scaffold_only", "partial", "ready"]


class OptionalEngineStatus(TypedDict):
    engine: str
    installed: bool
    status: EngineStatusValue
    role: str
    current_capability: str
    next_step: str
    safe_for_live: bool


ALLOWED_ENGINE_STATUSES = {"missing", "installed", "scaffold_only", "partial", "ready"}


def optional_engine_status(
    *,
    engine: str,
    installed: bool,
    status: EngineStatusValue,
    role: str,
    current_capability: str,
    next_step: str,
) -> OptionalEngineStatus:
    """Create a consistent optional-engine diagnostic object."""
    return {
        "engine": engine,
        "installed": installed,
        "status": status,
        "role": role,
        "current_capability": current_capability,
        "next_step": next_step,
        "safe_for_live": False,
    }

