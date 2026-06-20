# Remaining OpenBB Dashboard Issues

## Critical
None.

## High
None.

## Medium
None.

## Low / Future Work
1. Visual dashboard launch not verified.
   - Impact: Source and compile checks passed, but chart/table rendering in browser was not visually inspected.
   - Suggested action: Launch Streamlit manually and inspect page `10_openbb_ingestion`.

2. Annualized volatility currently applies only when `interval == "1d"`.
   - Impact: Other interval spellings or intraday intervals will not get annualized volatility.
   - Suggested action: Add interval normalization if more intervals are introduced.

3. CLI report writes a CSV to `reports/openbb/openbb_summary.csv`.
   - Impact: Expected runtime output, not a safety issue.
   - Suggested action: Keep under ignored/generated reports path.

4. Analytics are descriptive only.
   - Impact: Users may still overinterpret metrics.
   - Suggested action: Continue labeling dashboard as research context, not trading advice.
