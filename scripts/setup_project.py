from __future__ import annotations

import _bootstrap  # noqa: F401

from core.database import initialize_database
from core.paths import ensure_project_dirs


def main() -> None:
    ensure_project_dirs()
    path = initialize_database()
    print(f"Project initialized. Database: {path}")


if __name__ == "__main__":
    main()

