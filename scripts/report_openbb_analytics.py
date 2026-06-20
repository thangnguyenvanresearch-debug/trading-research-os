from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

import _bootstrap  # noqa: F401

from analytics.openbb_analytics import compute_openbb_data_quality, compute_openbb_return_summary, load_openbb_prices
from core.database import initialize_database
from core.paths import resolve_project_path


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print a local OpenBB analytics summary from the database.")
    parser.add_argument("--symbols", nargs="*", default=None, help="Optional symbols to include, e.g. AAPL MSFT.")
    parser.add_argument("--provider", default=None)
    parser.add_argument("--interval", default=None)
    parser.add_argument("--output", default="reports/openbb/openbb_summary.csv")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    initialize_database()
    prices = load_openbb_prices(symbols=args.symbols, provider=args.provider, interval=args.interval)
    summary = compute_openbb_return_summary(prices)
    quality = compute_openbb_data_quality(prices)
    if summary.empty:
        print("No local OpenBB market data found for the requested filters.")
    else:
        print(summary.to_string(index=False))
    print(
        "Data quality: "
        f"duplicates={quality['duplicate_timestamp_count']} "
        f"missing_close={quality['missing_close_count']} "
        f"non_positive_prices={quality['non_positive_prices']} "
        f"high_below_low={quality['high_below_low_count']}"
    )
    if args.output:
        output_path = resolve_project_path(Path(args.output))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        summary.to_csv(output_path, index=False)
        print(f"Wrote summary CSV: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
