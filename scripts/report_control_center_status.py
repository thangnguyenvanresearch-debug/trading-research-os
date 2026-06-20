from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
import _bootstrap  # noqa: F401,E402

from core.database import initialize_database  # noqa: E402
from dashboard.control_center import (  # noqa: E402
    build_next_actions,
    build_safety_checklist,
    get_latest_engine_statuses,
    write_control_center_report,
)


def main() -> int:
    initialize_database()
    result = write_control_center_report()
    statuses = get_latest_engine_statuses()
    print("Research Control Center")
    print(f"report_path={result['report_path']}")
    print("statuses=" + json.dumps(statuses, default=str))
    print(f"lean_executable_verified={statuses['lean']['executable_verified']}")
    print(f"daily_scheduler_state={statuses['latest_daily_run']['scheduler_state']}")
    checklist = build_safety_checklist()
    unsafe = checklist[checklist["status"] == "unsafe"] if not checklist.empty else checklist
    print(f"safety_unsafe_count={len(unsafe)}")
    print("next_actions=" + json.dumps(build_next_actions()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
