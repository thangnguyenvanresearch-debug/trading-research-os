from __future__ import annotations

import argparse
from collections.abc import Sequence

import _bootstrap  # noqa: F401

from pipeline.daily_research_pipeline import run_daily_research_pipeline


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local research-only daily pipeline.")
    parser.add_argument("--symbols", nargs="*", default=None, help="Symbols to research, e.g. AAPL MSFT.")
    parser.add_argument("--provider", default=None)
    parser.add_argument("--interval", default=None)
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--task-type", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--skip-ingest", action="store_true")
    parser.add_argument("--skip-ai", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    result = run_daily_research_pipeline(
        symbols=args.symbols,
        provider=args.provider,
        interval=args.interval,
        start_date=args.start_date,
        task_type=args.task_type,
        model=args.model,
        skip_ingest=args.skip_ingest,
        skip_ai=args.skip_ai,
        dry_run=args.dry_run,
    )
    print(f"run_id={result.run_id}")
    print(f"status={result.status}")
    print(f"symbols={','.join(result.symbols)}")
    print(f"provider={result.provider}")
    print(f"interval={result.interval}")
    print(f"analytics_report_path={result.analytics_report_path}")
    print(f"local_ai_memo_id={result.local_ai_memo_id}")
    print(f"local_ai_report_path={result.local_ai_report_path}")
    if result.warnings:
        print("warnings=" + "; ".join(str(warning) for warning in result.warnings))
    if result.errors:
        print("errors=" + "; ".join(str(error) for error in result.errors))
    return 0 if result.status not in {"failed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
