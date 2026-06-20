from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401

from freqtrade_brain.batch_backtest_runner import run_backtests


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Freqtrade or internal compatible backtests.")
    parser.add_argument("--use-freqtrade-cli", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Raise if Freqtrade CLI backtesting fails.")
    args = parser.parse_args()
    results = run_backtests(args.use_freqtrade_cli, strict=args.strict)
    for result in results:
        if result.get("status") == "failed_freqtrade_cli":
            print(f"{result['strategy_id']}: Freqtrade CLI failed: {result['error']}")
            continue
        print(
            f"{result['strategy_id']}: return={result['total_return']:.3f} "
            f"dd={result['max_drawdown']:.3f} trades={result['trade_count']}"
        )


if __name__ == "__main__":
    main()
