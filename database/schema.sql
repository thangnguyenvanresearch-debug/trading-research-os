CREATE TABLE IF NOT EXISTS assets (
  asset_id TEXT PRIMARY KEY,
  symbol TEXT NOT NULL,
  asset_class TEXT NOT NULL,
  exchange TEXT,
  quote_currency TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS market_data (
  symbol TEXT NOT NULL,
  timeframe TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  open REAL,
  high REAL,
  low REAL,
  close REAL,
  volume REAL,
  source TEXT NOT NULL,
  PRIMARY KEY (symbol, timeframe, timestamp, source)
);

CREATE TABLE IF NOT EXISTS openbb_market_data (
  id TEXT PRIMARY KEY,
  symbol TEXT NOT NULL,
  asset_class TEXT NOT NULL,
  provider TEXT NOT NULL,
  interval TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  open REAL,
  high REAL,
  low REAL,
  close REAL,
  volume REAL,
  adjusted_close REAL,
  source TEXT NOT NULL,
  retrieved_at TEXT NOT NULL,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS openbb_macro_data (
  id TEXT PRIMARY KEY,
  indicator TEXT NOT NULL,
  provider TEXT NOT NULL,
  frequency TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  value REAL,
  source TEXT NOT NULL,
  retrieved_at TEXT NOT NULL,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS openbb_ingestion_runs (
  run_id TEXT PRIMARY KEY,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL,
  requested_assets_json TEXT NOT NULL,
  provider_summary_json TEXT NOT NULL,
  rows_inserted INTEGER NOT NULL,
  rows_failed INTEGER NOT NULL,
  warnings_json TEXT NOT NULL,
  errors_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS openbb_research_context (
  id TEXT PRIMARY KEY,
  run_id TEXT,
  context_type TEXT NOT NULL,
  symbol TEXT,
  asset_class TEXT,
  provider TEXT NOT NULL,
  title TEXT,
  value_json TEXT NOT NULL,
  retrieved_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_research_memos (
  memo_id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  provider TEXT NOT NULL,
  model TEXT NOT NULL,
  task_type TEXT NOT NULL,
  symbols TEXT,
  source_context_json TEXT NOT NULL,
  prompt_text TEXT NOT NULL,
  response_text TEXT NOT NULL,
  status TEXT NOT NULL,
  warnings_json TEXT,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS daily_research_runs (
  run_id TEXT PRIMARY KEY,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL,
  symbols TEXT,
  provider TEXT,
  interval TEXT,
  task_type TEXT,
  openbb_ingestion_run_id TEXT,
  analytics_report_path TEXT,
  local_ai_memo_id TEXT,
  local_ai_report_path TEXT,
  warnings_json TEXT,
  errors_json TEXT,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS lean_backtest_runs (
  run_id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL,
  symbols TEXT,
  strategy_name TEXT,
  engine_status TEXT,
  command_text TEXT,
  project_path TEXT,
  report_path TEXT,
  metrics_json TEXT,
  warnings_json TEXT,
  errors_json TEXT,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS lean_backtest_metrics (
  metric_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  symbol TEXT,
  metric_name TEXT NOT NULL,
  metric_value REAL,
  metric_text TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS qlib_dataset_exports (
  export_id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  status TEXT NOT NULL,
  symbols TEXT,
  provider TEXT,
  interval TEXT,
  feature_count INTEGER,
  row_count INTEGER,
  output_path TEXT,
  manifest_path TEXT,
  warnings_json TEXT,
  errors_json TEXT,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS qlib_experiment_runs (
  run_id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL,
  symbols TEXT,
  experiment_name TEXT,
  qlib_available INTEGER,
  dataset_export_id TEXT,
  report_path TEXT,
  metrics_json TEXT,
  warnings_json TEXT,
  errors_json TEXT,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS qlib_predictions (
  prediction_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  symbol TEXT,
  timestamp TEXT,
  score REAL,
  label REAL,
  model_name TEXT,
  created_at TEXT NOT NULL,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS features (
  symbol TEXT NOT NULL,
  timeframe TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  feature_name TEXT NOT NULL,
  feature_value REAL,
  source TEXT NOT NULL,
  PRIMARY KEY (symbol, timeframe, timestamp, feature_name, source)
);

CREATE TABLE IF NOT EXISTS regimes (
  symbol TEXT NOT NULL,
  timeframe TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  regime TEXT NOT NULL,
  confidence REAL,
  details TEXT,
  PRIMARY KEY (symbol, timeframe, timestamp, regime)
);

CREATE TABLE IF NOT EXISTS strategy_specs (
  strategy_id TEXT PRIMARY KEY,
  strategy_name TEXT NOT NULL,
  asset_class TEXT NOT NULL,
  engine_target TEXT NOT NULL,
  spec_path TEXT NOT NULL,
  source_yaml TEXT NOT NULL,
  rationale TEXT,
  validation_status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  latest_review_at TEXT
);

CREATE TABLE IF NOT EXISTS generated_strategies (
  generated_id TEXT PRIMARY KEY,
  strategy_id TEXT NOT NULL,
  engine_target TEXT NOT NULL,
  code_path TEXT NOT NULL,
  template_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS backtest_runs (
  run_id TEXT PRIMARY KEY,
  strategy_id TEXT NOT NULL,
  engine TEXT NOT NULL,
  started_at TEXT NOT NULL,
  completed_at TEXT,
  status TEXT NOT NULL,
  result_path TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS backtest_metrics (
  run_id TEXT PRIMARY KEY,
  strategy_id TEXT NOT NULL,
  total_return REAL,
  out_of_sample_return REAL,
  max_drawdown REAL,
  sharpe REAL,
  sortino REAL,
  win_rate REAL,
  trade_count INTEGER,
  profit_factor REAL,
  avg_profit REAL,
  avg_win REAL,
  avg_loss REAL,
  best_pair TEXT,
  worst_pair TEXT,
  pair_level_metrics TEXT,
  fee_adjusted_return REAL,
  slippage_adjusted_return REAL,
  fee_slippage_adjusted_return REAL,
  pair_concentration REAL,
  regime_count INTEGER,
  equity_smoothness REAL,
  parser_warnings TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS risk_reviews (
  review_id TEXT PRIMARY KEY,
  strategy_id TEXT NOT NULL,
  run_id TEXT,
  status TEXT NOT NULL,
  flags TEXT NOT NULL,
  reviewed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS decisions (
  decision_id TEXT PRIMARY KEY,
  symbol TEXT NOT NULL,
  strategy_id TEXT NOT NULL,
  strategy_name TEXT NOT NULL,
  run_id TEXT,
  signal TEXT NOT NULL,
  permission TEXT NOT NULL,
  score REAL NOT NULL,
  regime TEXT,
  reasons TEXT NOT NULL,
  risk_flags TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS paper_trading_logs (
  log_id TEXT PRIMARY KEY,
  strategy_id TEXT NOT NULL,
  engine TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  event_type TEXT NOT NULL,
  payload TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS engine_runs (
  engine_run_id TEXT PRIMARY KEY,
  engine TEXT NOT NULL,
  command TEXT,
  status TEXT NOT NULL,
  started_at TEXT NOT NULL,
  completed_at TEXT,
  output_path TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS experiment_notes (
  note_id TEXT PRIMARY KEY,
  strategy_id TEXT,
  topic TEXT NOT NULL,
  note TEXT NOT NULL,
  created_at TEXT NOT NULL
);
