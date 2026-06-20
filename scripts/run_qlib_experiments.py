from __future__ import annotations

import _bootstrap  # noqa: F401

from qlib_brain.qlib_experiment_runner import run_basic_experiment


def main() -> None:
    print(run_basic_experiment())


if __name__ == "__main__":
    main()
