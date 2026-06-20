from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401

from data_brain.freqtrade_data_adapter import prepare_crypto_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Download or synthesize crypto OHLCV data.")
    parser.add_argument("--pairs", nargs="+", default=["BTC/USDT", "ETH/USDT", "SOL/USDT"])
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--candles", type=int, default=720)
    parser.add_argument("--sample", action="store_true", help="Generate explicitly labeled synthetic demo data.")
    parser.add_argument("--use-freqtrade-cli", action="store_true")
    args = parser.parse_args()
    paths = prepare_crypto_data(
        args.pairs,
        args.timeframe,
        args.candles,
        use_freqtrade_cli=args.use_freqtrade_cli,
        sample=args.sample,
    )
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
