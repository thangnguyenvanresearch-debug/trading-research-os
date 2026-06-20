# File-Level Findings Round 4

## `tests/test_no_lookahead.py`

Status: fixed.

Findings:

- Dedicated test exists for `x = df.close.shift(periods=-1)`.
- Test asserts `has_risk` and checks warnings/risk patterns for negative shift or look-ahead wording.
- Existing unsafe and safe AST tests remain present.

## `src/core/validation.py`

Status: accepted.

Findings:

- AST analyzer uses Python `ast` module.
- Analyzer statically parses source and walks AST.
- No dynamic import or execution of generated strategy code found in this analyzer.
- Keyword negative shift is supported via keyword names `periods` and `n`.

## `src/risk_brain/risk_gate.py`

Status: fixed.

Findings:

- `_lookahead_review()` returns `inspected_paths` sorted and deduplicated.
- `run_risk_reviews()` persists inspected paths into flags when look-ahead issues/warnings exist.
- Risk gate still rejects look-ahead risk.
- Dry-run divergence, archived status, approved_for_dry_run, and weak-metrics rejection remain present.

## `tests/test_risk_gate.py`

Status: fixed.

Findings:

- New test uses a temp database and temp generated strategy file with `shift(-1)`.
- It validates rejected status, presence of look-ahead audit flags, presence of inspected path flags, and no duplicate inspected path flags.

## `configs/engine_registry.yaml`

Status: fixed.

Findings:

- `finceptterminal.status` is now `scaffold_only`.
- `safe_for_live` remains false.
- Capability and next-step text clearly state future terminal-style analytics inspiration only.

## `src/core/engine_status.py`

Status: accepted.

Findings:

- Allowed statuses remain controlled: `missing`, `installed`, `scaffold_only`, `partial`, `ready`.
- `safe_for_live` is hardcoded false in optional engine status creation.

## `README.md`

Status: accepted.

Findings:

- README remains clear that live trading/futures/leverage/real orders are disabled.
- README describes FinceptTerminal as mentioned/future UI inspiration, not implemented functionality.
- README documents Freqtrade as the v1 focus and other engines as scaffold/future.
