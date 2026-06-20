from __future__ import annotations

import argparse
import json
from collections import Counter
from collections.abc import Sequence

import _bootstrap  # noqa: F401

from core.database import fetch_dataframe, initialize_database
from decision_brain.decision_engine import build_decisions
from risk_brain.risk_gate import run_risk_reviews


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run v1 risk reviews and print strategy decisions.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--latest-only",
        action="store_true",
        help="Print only decisions for the latest backtest run. Database history is preserved.",
    )
    group.add_argument(
        "--run-id",
        help="Print only decisions and risk reviews for a specific backtest run_id.",
    )
    return parser.parse_args(argv)


def latest_backtest_run_id() -> str | None:
    rows = fetch_dataframe("SELECT run_id FROM backtest_metrics ORDER BY created_at DESC, run_id DESC LIMIT 1")
    if rows.empty:
        return None
    return str(rows.iloc[0]["run_id"])


def filter_by_run_id(records: list[dict], run_id: str | None) -> list[dict]:
    if not run_id:
        return records
    return [record for record in records if str(record.get("run_id")) == run_id]


def format_decision(decision: dict) -> str:
    return (
        f"run_id={decision.get('run_id')} | "
        f"strategy={decision.get('strategy_name')} | "
        f"symbol={decision.get('symbol')} | "
        f"signal={decision.get('signal')} | "
        f"permission={decision.get('permission')} | "
        f"score={decision.get('score')} | "
        f"risk_flags={_top_risk_flags(decision.get('risk_flags'))}"
    )


def summarize_decisions(decisions: list[dict]) -> str:
    counts = Counter(str(decision.get("permission", "")).lower() for decision in decisions)
    return (
        "Summary: "
        f"decisions={len(decisions)} "
        f"rejected={counts.get('rejected', 0)} "
        f"watchlist={counts.get('watchlist', 0)} "
        f"paper_only={counts.get('paper_only', 0)} "
        f"approved_for_dry_run={counts.get('approved_for_dry_run', 0)}"
    )


def _top_risk_flags(raw_flags: object, limit: int = 2, max_length: int = 120) -> str:
    flags = _parse_flags(raw_flags)
    if not flags:
        return "none"
    selected = [_shorten(str(flag), max_length) for flag in flags[:limit]]
    if len(flags) > limit:
        selected.append(f"+{len(flags) - limit} more")
    return "; ".join(selected)


def _parse_flags(raw_flags: object) -> list[str]:
    if isinstance(raw_flags, list):
        return [str(flag) for flag in raw_flags]
    if isinstance(raw_flags, str) and raw_flags:
        try:
            parsed = json.loads(raw_flags)
        except json.JSONDecodeError:
            return [raw_flags]
        if isinstance(parsed, list):
            return [str(flag) for flag in parsed]
    return []


def _shorten(text: str, max_length: int) -> str:
    return text if len(text) <= max_length else f"{text[: max_length - 3]}..."


def selected_run_id(args: argparse.Namespace) -> str | None:
    if args.run_id:
        return args.run_id
    if args.latest_only:
        return latest_backtest_run_id()
    return None


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    initialize_database()
    reviews = run_risk_reviews()
    decisions = build_decisions()
    output_run_id = selected_run_id(args)
    if args.latest_only and output_run_id is None:
        print("No backtest runs found. Run backtests before scoring.")
    filtered_reviews = filter_by_run_id(reviews, output_run_id)
    filtered_decisions = filter_by_run_id(decisions, output_run_id)
    if output_run_id and not filtered_decisions:
        print(f"No decisions found for run_id={output_run_id}. Historical records were not modified.")
    print(f"Risk reviews printed: {len(filtered_reviews)}")
    for decision in filtered_decisions:
        print(format_decision(decision))
    print(summarize_decisions(filtered_decisions))


if __name__ == "__main__":
    main()
