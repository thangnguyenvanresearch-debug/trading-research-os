# Audit Round 4 Report

## Scope
Audit Round 4 chỉ kiểm tra cleanup sau Round 3:

- Keyword negative shift test coverage.
- Persist inspected look-ahead paths vào risk review flags.
- FinceptTerminal taxonomy alignment.
- Tests, compile, safe fallback workflow.
- Safety invariants và regression trong phạm vi thay đổi.

Không re-audit toàn bộ hệ thống Multi-Brain từ đầu.

## Commands Run
- `python --version`: Python 3.12.10.
- `python -m compileall src scripts -q`: passed, no compile errors.
- `python -m pytest -q`: 29 passed in 2.04s.
- `python scripts/init_database.py`: passed, SQLite fallback warning emitted because DuckDB unavailable.
- `python scripts/download_crypto_data.py --sample --pairs BTC/USDT ETH/USDT --timeframe 1h`: passed, imported 720 candles each for BTC/USDT and ETH/USDT with `source=sample_freqtrade_adapter`.
- `python scripts/build_features.py`: passed, built 1840 feature rows.
- `python scripts/generate_strategy_specs.py --asset-class crypto --count 3`: passed, generated 3 specs under `data/generated/specs`.
- `python scripts/convert_specs_to_freqtrade.py`: passed, generated 3 Freqtrade-compatible strategy files under `data/generated/freqtrade_strategies`.
- `python scripts/run_freqtrade_backtests.py`: passed, used internal fallback output for 3 strategies.
- `python scripts/score_strategies.py`: passed, produced risk reviews and rejected sample/fallback strategies.

## Safety Invariant Audit
Evidence:

- `configs/global.yaml` keeps all safety flags false.
- `src/core/models.py` defines permissions only as `REJECTED`, `WATCHLIST`, `PAPER_ONLY`, `APPROVED_FOR_DRY_RUN`.
- `tests/test_safe_defaults.py` asserts `APPROVED_FOR_LIVE` is absent and safety flags remain false.
- Safe search over `configs`, `src`, `scripts`, `tests` found `APPROVED_FOR_LIVE` only in tests that assert it is absent.
- No `create_order`, `place_order`, `market_order`, `limit_order`, `api_key`, `secret`, `private_key`, or `password` match was found in executable `configs/src/scripts` search scope.

Status: fixed / safe.

## Keyword Negative Shift Test Audit
Evidence:

- `tests/test_no_lookahead.py:27` defines `test_ast_detects_keyword_negative_shift`.
- The test calls `analyze_python_lookahead_risk("x = df.close.shift(periods=-1)")`.
- It asserts `review["has_risk"]` and checks messages for `negative pandas shift` or look-ahead wording.
- Existing tests remain for:
  - `df['close'].shift(-1)`.
  - `df.close.shift(-2)`.
  - `dataframe.iloc[i + 1]`.
  - `dataframe.iloc[index + n]`.
  - future-looking identifiers.
  - safe `shift(1)`, `rolling()`, `ewm()`.

`src/core/validation.py` still uses `ast.parse` and `ast.walk`. It does not execute strategy code and does not dynamically import generated strategy modules.

Status: fixed.

## Risk Inspected Path Persistence Audit
Evidence:

- `_lookahead_review()` in `src/risk_brain/risk_gate.py` still returns `inspected_paths` sorted and deduplicated.
- `run_risk_reviews()` now appends flags in the form `Look-ahead inspected path: <path>` when issues or warnings exist and inspected paths are available.
- Existing `Look-ahead audit:` and `Look-ahead warning:` flags are still preserved.
- `review_metrics()` still rejects strategies when `has_lookahead_risk` is true.
- Existing behaviors remain in place for dry-run divergence, archived status, approved_for_dry_run, and weak metrics rejection.
- `tests/test_risk_gate.py:94` adds a temporary DB test that writes a generated strategy containing `shift(-1)`, runs risk reviews, confirms rejected status, confirms inspected path flags exist, and confirms no duplicate inspected path flags.

Status: fixed.

## FinceptTerminal Taxonomy Audit
Evidence:

- `configs/engine_registry.yaml` now has `finceptterminal.status: scaffold_only`.
- It also includes:
  - `current_capability: Mentioned as future terminal-style analytics inspiration only.`
  - `next_step: Add a real FinceptTerminal adapter or UI shell in a future phase.`
  - `safe_for_live: false`.
- `src/core/engine_status.py` allows only `missing`, `installed`, `scaffold_only`, `partial`, `ready`.
- No fake FinceptTerminal adapter was added.
- README still describes FinceptTerminal as mentioned/future UX inspiration, which is honest. It is not claiming implemented functionality.

Status: fixed.

## Test Audit
Result: `29 passed`.

Coverage verified:

- Keyword negative shift: covered.
- Negative positional shift: covered.
- Future iloc offset: covered.
- Future-looking identifiers: covered.
- Safe indicator patterns: covered.
- Risk gate path persistence: covered with temporary DB.
- Dry-run divergence, archived, approved_for_dry_run: still covered.
- Safe defaults: covered.
- Optional engines missing do not crash: covered.

Status: accepted.

## Compile Audit
`python -m compileall src scripts -q` passed with no compile errors.

Status: accepted.

## Safe Workflow Audit
Safe fallback workflow passed end-to-end using sample data and internal fallback backtest. It did not run real exchange-connected Freqtrade download, Hummingbot live bot, Nautilus live execution, credential scripts, or order placement.

Observed output:

- Sample data imported as `sample_freqtrade_adapter`.
- Features built: 1840 rows.
- 3 YAML specs generated.
- 3 Freqtrade-compatible strategies generated under `data/generated`.
- Internal fallback backtest produced metrics for 3 strategies.
- Scoring rejected the sample/fallback strategies.

Note: `score_strategies.py` printed repeated decisions because the local database already contained historical runs. This is consistent with append/history behavior and not a Round 4 regression, but a future CLI cleanliness improvement could add a latest-run filter or a clean demo mode.

## Regression Audit
No regression detected in the audited Round 4 scope:

- AST analyzer still detects unsafe patterns and allows safe patterns.
- Risk gate still rejects look-ahead risk.
- Risk review flags now include inspected paths without dropping prior flags.
- FinceptTerminal registry is aligned with allowed taxonomy.
- Compile and pytest pass.
- Safe fallback workflow passes.
- Safety defaults remain disabled.

## Remaining Risks
No critical, high, or medium issues remain in Round 4 scope.

Planned future work remains:

- OpenBB full ingestion/context workflows.
- Qlib factor/ML experiments.
- LEAN portfolio backtests.
- Hummingbot paper/scanner lab hardening.
- NautilusTrader event-driven simulation path.
- FinceptTerminal real UI/terminal adapter or shell.

These are roadmap items, not remediation blockers.
