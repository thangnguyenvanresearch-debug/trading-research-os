# Fixed vs Unfixed Round 4

| Round 3 Remaining Issue | Claimed Round 4 Fix | Evidence Inspected | Status | Remaining Action |
|---|---|---|---|---|
| Missing pytest case for `shift(periods=-1)` | Added dedicated test in `tests/test_no_lookahead.py` | `tests/test_no_lookahead.py:27-31`; pytest 29 passed | fixed | None |
| Look-ahead inspected paths returned but not persisted into `risk_reviews.flags` | Added `Look-ahead inspected path: <path>` flags | `src/risk_brain/risk_gate.py:92-100`; `tests/test_risk_gate.py:94-159` | fixed | None |
| FinceptTerminal status used `mentioned_only`, not in allowed taxonomy | Changed config status to `scaffold_only` and added capability/next step | `configs/engine_registry.yaml:8-15`; `src/core/engine_status.py` allowed statuses | fixed | None |
| Optional engines remain scaffold/future | No full integration attempted | README and engine registry remain honest; Freqtrade remains v1 path | planned future work | Build integrations in later phases only if needed |
