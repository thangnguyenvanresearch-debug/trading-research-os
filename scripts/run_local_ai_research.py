from __future__ import annotations

import argparse
from collections.abc import Sequence

import _bootstrap  # noqa: F401

from ai.research_engine import ALLOWED_TASKS, run_local_ai_research
from core.config_loader import load_config
from core.database import initialize_database


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local-only Ollama research analysis from database rows.")
    parser.add_argument("--symbols", nargs="*", default=None, help="Symbols to include, e.g. AAPL MSFT.")
    parser.add_argument("--provider", default=None, help="Optional local data provider filter, e.g. yfinance.")
    parser.add_argument("--interval", default=None, help="Optional interval filter, e.g. 1d.")
    parser.add_argument("--task-type", default="market_review", choices=sorted(ALLOWED_TASKS))
    parser.add_argument("--include-backtests", action="store_true")
    parser.add_argument("--include-risk", action="store_true")
    parser.add_argument("--include-decisions", action="store_true")
    parser.add_argument("--model", default=None)
    parser.add_argument("--base-url", default=None)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    initialize_database()
    config = load_config("local_ai")
    if args.model:
        config["model"] = args.model
    if args.base_url:
        config["base_url"] = args.base_url
    result = run_local_ai_research(
        symbols=args.symbols,
        provider=args.provider,
        interval=args.interval,
        task_type=args.task_type,
        include_openbb=True,
        include_backtests=args.include_backtests,
        include_risk=args.include_risk,
        include_decisions=args.include_decisions,
        config=config,
    )
    print(f"memo_id={result['memo_id']}")
    print(f"status={result['status']}")
    print(f"provider={result['provider']}")
    print(f"model={result['model']}")
    print(f"output_path={result['output_path']}")
    if result.get("error"):
        print(f"error={result['error']}")
    if result.get("warnings"):
        print("warnings=" + "; ".join(str(warning) for warning in result["warnings"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
