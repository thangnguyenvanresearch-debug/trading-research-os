from __future__ import annotations

from core.database import fetch_dataframe


def list_strategies():
    return fetch_dataframe("SELECT * FROM strategy_specs ORDER BY created_at DESC")

