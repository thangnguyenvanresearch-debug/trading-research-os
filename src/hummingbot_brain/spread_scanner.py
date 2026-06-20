from __future__ import annotations

import importlib.util

from core.engine_status import OptionalEngineStatus, optional_engine_status


def get_hummingbot_status() -> OptionalEngineStatus:
    installed = importlib.util.find_spec("hummingbot") is not None
    return optional_engine_status(
        engine="hummingbot",
        installed=installed,
        status="partial",
        role="Paper-only market making, spread monitoring, and arbitrage lab.",
        current_capability="Local spread math, inventory simulation, arbitrage scoring, and paper config generation.",
        next_step="Add order book snapshot ingestion and paper-only connector diagnostics.",
    )


def scan_spread(symbol: str, bid: float, ask: float, fee_rate: float = 0.001) -> dict:
    mid = (bid + ask) / 2 if bid and ask else 0
    gross = (ask - bid) / mid if mid else 0
    net = gross - fee_rate * 2
    return {"symbol": symbol, "gross_spread": gross, "fee_adjusted_spread": net, "status": "alert_only"}
