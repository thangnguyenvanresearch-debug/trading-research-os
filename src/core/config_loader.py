from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from core.paths import CONFIG_DIR, resolve_project_path


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML file from an absolute or project-relative path."""
    resolved = resolve_project_path(path)
    with resolved.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_config(name: str) -> dict[str, Any]:
    """Load a file from configs by name, with or without .yaml."""
    filename = name if name.endswith(".yaml") else f"{name}.yaml"
    return load_yaml(CONFIG_DIR / filename)


def load_global_config() -> dict[str, Any]:
    return load_config("global")

