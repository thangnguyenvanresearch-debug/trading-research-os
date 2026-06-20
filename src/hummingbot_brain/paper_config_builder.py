from __future__ import annotations

import yaml
from pathlib import Path

from core.paths import DATA_DIR


def build_paper_config(name: str, connector: str, pair: str) -> Path:
    config = {"name": name, "connector": connector, "pair": pair, "paper_only": True, "live_trading": False}
    path = DATA_DIR / "hummingbot" / f"{name}.paper.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return path

