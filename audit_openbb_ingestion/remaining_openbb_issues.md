# Remaining OpenBB Issues

## Critical
None.

## High
None.

## Medium
None verified.

## Low
1. Real OpenBB ingestion is not runtime-verified.
   - Reason: OpenBB package is not installed in this environment.
   - Impact: Adapter structure is validated by mocks, but provider-specific API compatibility remains unknown.
   - Fix: In an environment with OpenBB installed, run a no-key provider smoke test and add fixture-based compatibility tests.

2. `src/feature_brain/openbb_feature_bridge.py` is not defensive against missing OpenBB tables.
   - Reason: It directly queries `openbb_market_data` and assumes DB initialization happened earlier.
   - Impact: A direct caller could see a database missing-table error.
   - Fix: Initialize DB in caller or add a small guard/helper that returns an empty DataFrame on missing-table errors.

3. `src/data_brain/openbb_adapter.py` is large.
   - Reason: It contains detection, fetch, normalization, persistence, file output, and context code.
   - Impact: Maintainability risk as provider support expands.
   - Fix: Later split into `openbb_fetchers.py`, `openbb_normalizer.py`, and `openbb_storage.py` if complexity grows.

4. Malformed provider output without timestamp/date can create RangeIndex string timestamps.
   - Reason: `_timestamp_series()` falls back to positional strings.
   - Impact: Bad provider data may be stored with weak timestamps instead of being rejected.
   - Fix: Emit a warning or fail that symbol when no timestamp-like column exists.

## Not Remediation Blockers
- OpenBB, Qlib, LEAN, Hummingbot, Nautilus remain optional and not live-trading engines.
- Macro provider coverage is intentionally best-effort for this phase.
