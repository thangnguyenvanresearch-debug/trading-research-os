# Remaining Issues Round 4

## Critical Issues
None.

## High Issues
None.

## Medium Issues
None.

## Low Issues
None requiring remediation from Round 4 cleanup.

## Observations
`score_strategies.py` produced repeated decision lines because the local database contained accumulated historical runs. This was observed during the safe workflow and is not a Round 4 regression. Future CLI ergonomics could add a latest-run filter or clean-demo mode.

## Planned Future Work
The following remain future roadmap items, not remediation blockers:

- OpenBB: fuller data/context ingestion.
- Qlib: real factor/ML experiment workflows.
- LEAN: real portfolio/equity/ETF backtest runner integration.
- Hummingbot: deeper paper/scanner lab.
- NautilusTrader: event-driven simulation adapter.
- FinceptTerminal: real terminal-style analytics/UI shell if desired.
