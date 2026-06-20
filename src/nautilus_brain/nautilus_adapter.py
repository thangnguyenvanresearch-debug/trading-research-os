from __future__ import annotations

import importlib.util

from core.engine_status import OptionalEngineStatus, optional_engine_status


def nautilus_status() -> dict:
    available = importlib.util.find_spec("nautilus_trader") is not None
    return {
        "available": available,
        "role": "future v2 event-driven architecture target",
        "live_enabled": False,
    }


def get_nautilus_status() -> OptionalEngineStatus:
    installed = importlib.util.find_spec("nautilus_trader") is not None
    return optional_engine_status(
        engine="nautilus",
        installed=installed,
        status="scaffold_only",
        role="Future event-driven production-grade simulation architecture target.",
        current_capability="Availability check, event dataclass, skeleton notes, and simulation placeholder.",
        next_step="Map validated YAML specs to Nautilus simulation components in v2.",
    )
