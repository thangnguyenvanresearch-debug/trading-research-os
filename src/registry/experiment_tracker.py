from __future__ import annotations

from core.database import insert_dict, new_id, utc_now


def add_note(topic: str, note: str, strategy_id: str | None = None) -> str:
    note_id = new_id("note")
    insert_dict(
        "experiment_notes",
        {
            "note_id": note_id,
            "strategy_id": strategy_id,
            "topic": topic,
            "note": note,
            "created_at": utc_now(),
        },
    )
    return note_id

