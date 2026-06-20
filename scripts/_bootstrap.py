from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.config_loader import load_global_config  # noqa: E402
from core.validation import assert_research_only  # noqa: E402


assert_research_only(load_global_config())
