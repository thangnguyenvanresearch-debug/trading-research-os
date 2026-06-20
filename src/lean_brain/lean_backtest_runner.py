from __future__ import annotations

from lean_brain.lean_adapter import get_lean_status


def lean_cli_status() -> dict:
    status = get_lean_status()
    return {
        "available": status["lean_cli_available"],
        "message": "LEAN CLI available." if status["lean_cli_available"] else "LEAN CLI not installed.",
    }
