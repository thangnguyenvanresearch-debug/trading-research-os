from __future__ import annotations

import json
from pathlib import Path

from core.paths import DATA_DIR


def build_dry_run_config(pairs: list[str]) -> Path:
    """Create a dry-run-only Freqtrade config. It never enables real orders."""
    config = {
        "dry_run": True,
        "trading_mode": "spot",
        "margin_mode": "",
        "stake_currency": "USDT",
        "stake_amount": "unlimited",
        "max_open_trades": 3,
        "exchange": {"name": "binance", "pair_whitelist": pairs, "pair_blacklist": []},
        "api_server": {"enabled": False},
        "force_entry_enable": False,
    }
    path = DATA_DIR / "freqtrade" / "config.dry-run.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return path
