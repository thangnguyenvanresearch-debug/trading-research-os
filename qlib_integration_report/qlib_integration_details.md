# Qlib Integration Details

## Implementation

Added Qlib as an optional research-only ML/factor engine.

The integration uses local OpenBB rows from `openbb_market_data` and never fetches remote Qlib datasets by default. If Qlib is missing, the system still exports the dataset and records an `unavailable` experiment run without crashing.

## New Configuration

`configs/qlib.yaml`:

- `mode: research_only`
- `safe_for_live: false`
- all unsafe flags false:
  - `allow_live_trading`
  - `allow_real_orders`
  - `allow_brokerage_credentials`
  - `allow_cloud_credentials`
  - `allow_futures`
  - `allow_leverage`

`configs/daily_research.yaml`:

- added Qlib block
- `enabled: false`
- Qlib is not run by the daily pipeline by default

## Database

Added tables:

- `qlib_dataset_exports`
- `qlib_experiment_runs`
- `qlib_predictions`

CLI smoke created rows in:

- `qlib_dataset_exports`
- `qlib_experiment_runs`

`qlib_predictions` remains empty because Qlib is unavailable and no real predictions were produced.

## Feature Dataset

Feature columns include:

- `open`
- `high`
- `low`
- `close`
- `volume`
- `close_return_1d`
- `close_return_5d`
- `momentum_20d`
- `volatility_20d`
- `volume_zscore_20d`

Label:

- `label_forward_return_5d`

Look-ahead handling:

- Features use current/trailing data.
- Future return is stored only in the label column.
- Manifest states this separation explicitly.

Latest feature verification:

```text
features.csv shape: (2220, 13)
symbols: AAPL/MSFT from local OpenBB data
```

## Commands Run

Compile:

```powershell
python -m compileall src scripts -q
python -m compileall src\dashboard -q
```

Result: passed.

Tests:

```powershell
python -m pytest -q
```

Result:

```text
120 passed in 22.72s
```

Qlib availability:

```powershell
python -c "import importlib.util; print('qlib_installed=' + str(importlib.util.find_spec('qlib') is not None))"
```

Result:

```text
qlib_installed=False
```

Dataset export smoke:

```powershell
python scripts\run_qlib_experiment.py --symbols AAPL MSFT --provider yfinance --interval 1d --experiment-name qlib_demo --skip-run
```

Result:

```text
run_id=qlib_run_c6644c34575e
status=dataset_exported
dataset_export_id=qlib_export_30eb157bd51d
metrics_count=0
predictions_count=0
```

Normal unavailable path:

```powershell
python scripts\run_qlib_experiment.py --symbols AAPL MSFT --provider yfinance --interval 1d --experiment-name qlib_demo
```

Result:

```text
run_id=qlib_run_01399ff0a449
status=unavailable
dataset_export_id=qlib_export_69643487871e
metrics_count=0
predictions_count=0
warnings=["Qlib is not installed; dataset export works, but Qlib execution is unavailable."]
errors=[]
```

DB verification:

- latest exports are visible in `qlib_dataset_exports`
- latest runs are visible in `qlib_experiment_runs`
- `qlib_predictions` is empty

Dashboard HTTP:

```text
URLError: [WinError 10061] connection refused
```

Interpretation: Streamlit was not running. This is not a Qlib source failure.

Safety grep:

- No unsafe enablement found.
- Hits are expected docs/tests/config false flags and safety blocklists.

## Remaining Issues

1. Qlib package is not installed, so executable Qlib ML experiment is not verified.
2. Dashboard visual inspection was not performed because Streamlit was not running.
3. The implemented "Qlib available" branch currently runs a clearly labeled pandas baseline placeholder. Full Qlib trainer integration remains future work.
