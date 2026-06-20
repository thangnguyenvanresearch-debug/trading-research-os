from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401

from ai_strategy_brain.strategy_generator import generate_specs, write_specs
from core.database import initialize_database


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate structured YAML strategy specs.")
    parser.add_argument("--asset-class", default="crypto")
    parser.add_argument("--count", type=int, default=3)
    parser.add_argument("--pairs", nargs="+", default=["BTC/USDT", "ETH/USDT", "SOL/USDT"])
    args = parser.parse_args()
    initialize_database()
    paths = write_specs(generate_specs(args.asset_class, args.count, args.pairs))
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()

