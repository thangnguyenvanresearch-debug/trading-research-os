from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
import _bootstrap  # noqa: F401,E402

from core.database import initialize_database  # noqa: E402
from lean_brain.lean_runner import run_lean_backtest  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create/run a research-only local LEAN backtest skeleton.")
    parser.add_argument("--symbols", nargs="+", default=["AAPL", "MSFT"])
    parser.add_argument("--provider", default="yfinance")
    parser.add_argument("--interval", default="1d")
    parser.add_argument("--strategy-name", default="equal_weight_demo")
    parser.add_argument("--cash", type=float, default=100000)
    parser.add_argument("--skip-run", action="store_true", help="Create local data/project skeleton only.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    initialize_database()
    result = run_lean_backtest(
        symbols=args.symbols,
        provider=args.provider,
        interval=args.interval,
        strategy_name=args.strategy_name,
        cash=args.cash,
        skip_run=args.skip_run,
    )
    print(f"run_id={result['run_id']}")
    print(f"status={result['status']}")
    print(f"project_path={result['project_path']}")
    print(f"report_path={result['report_path']}")
    print(f"warnings={json.dumps(result['warnings'])}")
    print(f"errors={json.dumps(result['errors'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
