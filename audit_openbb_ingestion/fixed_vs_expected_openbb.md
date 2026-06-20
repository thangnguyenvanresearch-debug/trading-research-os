# Fixed vs Expected OpenBB

| Expected Capability | Evidence Inspected | Status | Notes |
|---|---|---|---|
| Safe OpenBB config | `configs/openbb.yaml` | implemented | `safe_mode: true`, `allow_credentials: false`, DB/file write flags present. |
| Engine registry not scaffold-only | `configs/engine_registry.yaml` | implemented | OpenBB is `partial`, `safe_for_live: false`, `execution_allowed: false`. |
| OpenBB market table | `database/schema.sql` | implemented | `openbb_market_data` exists. |
| OpenBB macro table | `database/schema.sql` | implemented | `openbb_macro_data` exists. |
| Ingestion run tracking | `database/schema.sql` | implemented | `openbb_ingestion_runs` exists. |
| Research context table | `database/schema.sql` | implemented | `openbb_research_context` exists, but current context function returns summaries rather than persisting context rows. |
| Missing package does not crash | CLI command and tests | implemented | CLI exits 0 by default with clear message. |
| Normalize OHLCV columns | `normalize_openbb_market_data`, tests | implemented | Required normalized columns covered. |
| One symbol failure does not kill run | `tests/test_openbb_adapter.py` | implemented | Success + failure tested. |
| Local file output | `_write_frame()` | implemented | Parquet attempted, CSV fallback. Not exercised in real OpenBB run. |
| Macro ingestion | `ingest_openbb_macro_data()` | partially implemented | Best-effort structure exists; real provider behavior not verified. |
| Dashboard display | `src/dashboard/pages/10_openbb_ingestion.py` | implemented | Reads DB only. |
| Feature bridge | `src/feature_brain/openbb_feature_bridge.py` | partially implemented | Converts shape; missing-table guard absent. |
| Real OpenBB provider ingestion | OpenBB package check | not verifiable | OpenBB is not installed. |
