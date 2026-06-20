# Remaining Issues Round 3

## Critical

Không phát hiện critical issue.

## High

Không phát hiện high issue.

## Medium

Không có medium issue mới ảnh hưởng v1 safety hoặc fallback research workflow.

## Low

### 1. Missing pytest case for keyword negative shift

- File: `tests/test_no_lookahead.py`
- Evidence: tests cover `df['close'].shift(-1)`, `df.close.shift(-2)`, `dataframe.iloc[i + 1]`, `dataframe.iloc[index + n]`, future variable names, and safe `shift(1)/rolling/ewm`.
- Gap: không có test pytest riêng cho `shift(periods=-1)`.
- Verification: ad-hoc command with `PYTHONPATH=src` confirmed `x=df.close.shift(periods=-1)` returns `has_risk: True`.
- Why it matters: requirement audit explicitly listed keyword negative shift; adding test would prevent future regression.

### 2. Inspected paths not persisted into risk review flags

- File: `src/risk_brain/risk_gate.py`
- Evidence: `_lookahead_review()` returns `inspected_paths`, including `spec_path` and generated `code_path`.
- Gap: `run_risk_reviews()` stores look-ahead issues/warnings in `flags`, but not `inspected_paths`.
- Why it matters: dashboard/user can see the risk pattern but not immediately the exact inspected file path from `risk_reviews.flags`.
- Severity: low; internal hook already returns paths.

### 3. FinceptTerminal taxonomy is honest but not standardized in code

- File: `configs/engine_registry.yaml`, `README.md`
- Evidence: config uses `status: mentioned_only`; README states `mentioned only / future`.
- Gap: `src/core/engine_status.py` allowed statuses do not include `mentioned_only`, and there is no FinceptTerminal status helper.
- Why it matters: diagnostics are standardized for OpenBB/Qlib/LEAN/Hummingbot/Nautilus, not for FinceptTerminal. This is not unsafe because no Fincept module is claimed.

### 4. Optional engines remain scaffold/future

- Files: `src/data_brain/openbb_adapter.py`, `src/qlib_brain/`, `src/lean_brain/`, `src/hummingbot_brain/`, `src/nautilus_brain/`
- Evidence: status objects honestly report scaffold_only or partial; no production integration added.
- Why it matters: users cannot run actual OpenBB ingestion, Qlib ML experiments, LEAN portfolio backtests, or Nautilus simulation yet.
- Severity: low/planned; this was explicitly out of scope for Round 3.

