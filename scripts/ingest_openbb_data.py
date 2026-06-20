from __future__ import annotations

import argparse
from collections.abc import Sequence

import _bootstrap  # noqa: F401

from core.config_loader import load_config
from core.database import initialize_database
from data_brain.openbb_adapter import (
    detect_openbb,
    get_openbb_research_context,
    ingest_openbb_macro_data,
    ingest_openbb_market_data,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    config = load_config("openbb")
    parser = argparse.ArgumentParser(description="Ingest OpenBB research data into local storage.")
    parser.add_argument("--symbols", nargs="+", default=None, help="Symbols such as AAPL MSFT NVDA.")
    parser.add_argument("--asset-class", default="equity", choices=["equity", "etf", "crypto"])
    parser.add_argument("--start-date", default=config.get("default_start_date", "2022-01-01"))
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--interval", default=config.get("default_interval", "1d"))
    parser.add_argument("--provider", default=None)
    parser.add_argument("--macro", nargs="*", help="Optional macro indicators to ingest, such as GDP CPI.")
    parser.add_argument("--sample-context", action="store_true", help="Print local OpenBB context after ingestion.")
    parser.add_argument("--no-write-db", action="store_true", help="Do not write normalized data to the database.")
    parser.add_argument("--no-write-parquet", action="store_true", help="Do not write normalized data files.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when OpenBB is missing.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    initialize_database()
    config = load_config("openbb")
    symbols = args.symbols or _default_symbols(config, args.asset_class)
    write_db = not args.no_write_db and bool(config.get("write_to_database", True))
    write_parquet = not args.no_write_parquet and bool(config.get("write_to_parquet", True))

    if not detect_openbb():
        message = "OpenBB is not installed. Install optional OpenBB support or keep using Freqtrade/sample workflow."
        print(message)
        return 1 if args.strict else 0

    market = ingest_openbb_market_data(
        symbols=symbols,
        asset_class=args.asset_class,
        start_date=args.start_date,
        end_date=args.end_date,
        interval=args.interval,
        provider=args.provider,
        write_db=write_db,
        write_parquet=write_parquet,
    )
    print_result("market", market.to_dict())

    if args.macro is not None:
        indicators = args.macro or ["GDP", "CPI"]
        macro = ingest_openbb_macro_data(
            indicators=indicators,
            start_date=args.start_date,
            end_date=args.end_date,
            provider=args.provider,
            write_db=write_db,
            write_parquet=write_parquet,
        )
        print_result("macro", macro.to_dict())

    if args.sample_context:
        context = get_openbb_research_context(symbols, [args.asset_class], include_macro=args.macro is not None)
        print(f"Local OpenBB context rows: {len(context)}")
        for row in context[:5]:
            print(row)
    return 0


def print_result(label: str, result: dict) -> None:
    print(f"OpenBB {label} ingestion run_id={result['run_id']} status={result['status']}")
    print(f"rows_inserted={result['rows_inserted']} rows_failed={result['rows_failed']}")
    print(f"provider_summary={result['provider_summary']}")
    if result.get("output_paths"):
        print("output_paths:")
        for path in result["output_paths"]:
            print(f"  {path}")
    if result.get("warnings"):
        print("warnings:")
        for warning in result["warnings"]:
            print(f"  {warning}")
    if result.get("errors"):
        print("errors:")
        for error in result["errors"]:
            print(f"  {error}")


def _default_symbols(config: dict, asset_class: str) -> list[str]:
    universe = config.get("default_universe", {})
    if asset_class == "crypto":
        return list(universe.get("crypto", ["BTC-USD", "ETH-USD"]))
    if asset_class == "etf":
        return list(universe.get("etfs", ["SPY", "QQQ"]))
    return list(universe.get("equities", ["AAPL", "MSFT", "NVDA"]))


if __name__ == "__main__":
    raise SystemExit(main())
