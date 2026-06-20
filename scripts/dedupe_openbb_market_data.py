from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
import _bootstrap  # noqa: F401,E402

from core.database import execute, fetch_dataframe, initialize_database, utc_now  # noqa: E402
from core.paths import REPORTS_DIR, resolve_project_path  # noqa: E402
from core.validation import assert_research_only  # noqa: E402
from core.config_loader import load_config  # noqa: E402


DUPLICATE_KEY_COLUMNS = ["symbol", "asset_class", "provider", "interval", "timestamp"]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dry-run or apply dedupe for local OpenBB market rows.")
    parser.add_argument("--apply", action="store_true", help="Delete duplicate rows after backing them up.")
    parser.add_argument("--limit", type=int, default=50, help="Maximum duplicate groups to print in dry-run output.")
    return parser.parse_args(argv)


def find_duplicate_groups(limit: int = 50) -> pd.DataFrame:
    return fetch_dataframe(
        f"""
        SELECT {", ".join(DUPLICATE_KEY_COLUMNS)}, COUNT(*) AS duplicate_count
        FROM openbb_market_data
        GROUP BY {", ".join(DUPLICATE_KEY_COLUMNS)}
        HAVING COUNT(*) > 1
        ORDER BY duplicate_count DESC, symbol, timestamp
        LIMIT ?
        """,
        (limit,),
    )


def apply_dedupe() -> dict[str, object]:
    rows = fetch_dataframe(
        f"""
        SELECT id, {", ".join(DUPLICATE_KEY_COLUMNS)}, retrieved_at
        FROM openbb_market_data
        WHERE ({", ".join(DUPLICATE_KEY_COLUMNS)}) IN (
            SELECT {", ".join(DUPLICATE_KEY_COLUMNS)}
            FROM openbb_market_data
            GROUP BY {", ".join(DUPLICATE_KEY_COLUMNS)}
            HAVING COUNT(*) > 1
        )
        ORDER BY symbol, asset_class, provider, interval, timestamp, retrieved_at DESC, id
        """
    )
    if rows.empty:
        return {"duplicates_found": 0, "rows_deleted": 0, "backup_path": None}

    backup_dir = resolve_project_path(REPORTS_DIR / "maintenance")
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"openbb_market_data_duplicates_{utc_now().replace(':', '').replace('+', '_')}.csv"
    rows.to_csv(backup_path, index=False)

    keep_ids = set()
    delete_ids = []
    for _, group in rows.groupby(DUPLICATE_KEY_COLUMNS, dropna=False):
        ordered = group.sort_values(["retrieved_at", "id"], ascending=[False, True])
        keep_ids.add(str(ordered.iloc[0]["id"]))
        delete_ids.extend(str(value) for value in ordered.iloc[1:]["id"].tolist())

    for row_id in delete_ids:
        execute("DELETE FROM openbb_market_data WHERE id = ?", (row_id,))

    return {
        "duplicates_found": int(len(rows)),
        "rows_deleted": int(len(delete_ids)),
        "rows_kept": int(len(keep_ids)),
        "backup_path": str(backup_path),
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    assert_research_only(load_config("global"))
    initialize_database()
    if not args.apply:
        groups = find_duplicate_groups(args.limit)
        print("OpenBB market data dedupe dry-run. No rows were deleted.")
        if groups.empty:
            print("No duplicate groups found.")
        else:
            print(groups.to_string(index=False))
        return 0

    result = apply_dedupe()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
