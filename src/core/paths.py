from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "configs"
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_DIR = PROJECT_ROOT / "database"
REPORTS_DIR = PROJECT_ROOT / "reports"
SRC_DIR = PROJECT_ROOT / "src"


def resolve_project_path(path: str | Path) -> Path:
    """Resolve a project-relative path without hardcoding local absolute paths."""
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return PROJECT_ROOT / candidate


def ensure_project_dirs() -> None:
    """Create runtime directories expected by the v1 pipeline."""
    for directory in [
        DATA_DIR / "raw",
        DATA_DIR / "processed",
        DATA_DIR / "features",
        DATA_DIR / "openbb",
        DATA_DIR / "freqtrade",
        DATA_DIR / "lean",
        DATA_DIR / "qlib",
        DATA_DIR / "hummingbot",
        DATA_DIR / "nautilus",
        DATA_DIR / "generated",
        DATA_DIR / "generated" / "specs",
        DATA_DIR / "generated" / "freqtrade_strategies",
        REPORTS_DIR / "backtests",
        REPORTS_DIR / "freqtrade",
        REPORTS_DIR / "lean",
        REPORTS_DIR / "qlib",
        REPORTS_DIR / "hummingbot",
        REPORTS_DIR / "nautilus",
        REPORTS_DIR / "local_ai",
        REPORTS_DIR / "daily_research",
        REPORTS_DIR / "weekly_reviews",
    ]:
        directory.mkdir(parents=True, exist_ok=True)
