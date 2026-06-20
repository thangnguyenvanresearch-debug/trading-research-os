# Fixed vs Unfixed Round 3

| Round 2 remaining issue | Claimed Round 3 fix | Evidence inspected | Status | Remaining action |
|---|---|---|---|---|
| Optional engines ngoài Freqtrade scaffold-only | Standardized optional engine status objects with `safe_for_live: false` | `src/core/engine_status.py`; `get_openbb_status`, `get_qlib_status`, `get_lean_status`, `get_hummingbot_status`, `get_nautilus_status`; dashboard pages | fixed | Optional: add FinceptTerminal status helper or dashboard row if desired. |
| Look-ahead detection dùng substring matching | AST-based static analysis added | `src/core/validation.py` imports `ast`, defines `analyze_python_lookahead_risk`; tests in `tests/test_no_lookahead.py`; ad-hoc command verified `shift(periods=-1)` | fixed | Add pytest case for keyword negative shift to lock coverage. |
| DuckDB fallback thiếu console warning | Logger warning added, once per process | `src/core/database.py` `SQLITE_FALLBACK_WARNING`, `_warn_sqlite_fallback_once`; `tests/test_database_fallback.py`; safe workflow output showed warning | fixed | Không cần fix cấp bách. |
| Risk gate should consume AST/substr findings | `_lookahead_review()` uses `contains_forbidden_logic(... analyze_python=True)` and `analyze_python_lookahead_risk(... strict=True)` | `src/risk_brain/risk_gate.py`; `tests/test_risk_gate.py` | fixed / minor partial | Persist inspected paths into risk flags for easier dashboard/debug if look-ahead fires. |
| Dashboard should be honest about scaffold engines | Dashboard uses standardized statuses | `src/dashboard/streamlit_app.py`, pages 06/07/09 | fixed | Optional: show FinceptTerminal mentioned-only status. |
| README should document Round 3 | Round 3 Hardening section added | `README.md` | fixed | Không cần fix. |

