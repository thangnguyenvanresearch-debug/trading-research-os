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
from qlib_brain.qlib_runner import run_qlib_experiment  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a research-only local Qlib dataset/experiment workflow.")
    parser.add_argument("--symbols", nargs="+", default=["AAPL", "MSFT"])
    parser.add_argument("--provider", default="yfinance")
    parser.add_argument("--interval", default="1d")
    parser.add_argument("--experiment-name", default="qlib_demo")
    parser.add_argument("--horizon-days", type=int, default=5)
    parser.add_argument("--skip-run", action="store_true", help="Export dataset only; do not attempt Qlib execution.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    initialize_database()
    result = run_qlib_experiment(
        symbols=args.symbols,
        provider=args.provider,
        interval=args.interval,
        experiment_name=args.experiment_name,
        horizon_days=args.horizon_days,
        skip_run=args.skip_run,
    )
    print(f"run_id={result['run_id']}")
    print(f"status={result['status']}")
    print(f"dataset_export_id={result['dataset_export_id']}")
    print(f"features_path={result['features_path']}")
    print(f"manifest_path={result['manifest_path']}")
    print(f"report_path={result['report_path']}")
    print(f"metrics_count={len(result['metrics'])}")
    print(f"predictions_count={result['predictions_count']}")
    print(f"warnings={json.dumps(result['warnings'])}")
    print(f"errors={json.dumps(result['errors'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
