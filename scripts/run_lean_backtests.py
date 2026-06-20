from __future__ import annotations

import _bootstrap  # noqa: F401

from lean_brain.lean_backtest_runner import lean_cli_status


def main() -> None:
    print(lean_cli_status())


if __name__ == "__main__":
    main()

