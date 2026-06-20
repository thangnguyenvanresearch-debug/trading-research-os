from __future__ import annotations

import _bootstrap  # noqa: F401

from core.database import initialize_database
from freqtrade_brain.freqtrade_strategy_converter import convert_all_specs


def main() -> None:
    initialize_database()
    paths = convert_all_specs()
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()

