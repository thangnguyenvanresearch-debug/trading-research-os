# Regression Check Round 4

Không phát hiện regression.

Verified:

- AST look-ahead analyzer still detects positional negative shift, keyword negative shift, future iloc access, and future-looking identifiers.
- Safe patterns `shift(1)`, `rolling()`, and `ewm()` remain allowed by tests.
- Risk gate still rejects look-ahead risk.
- Risk review flags now include inspected paths while preserving existing issue/warning flags.
- FinceptTerminal config status no longer uses unsupported `mentioned_only` taxonomy.
- Compile passed.
- Pytest passed: 29 tests.
- Safe fallback workflow passed.
- No live trading, futures, leverage, or real orders were enabled.
