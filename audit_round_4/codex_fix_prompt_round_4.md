# Codex Fix Prompt Round 4

## Optional Future Development Prompt

There are no critical, high, medium, or required low-priority remediation issues left from Round 4.

Use this only as an optional future development prompt, not a bugfix prompt.

```
You are Codex working in D:\AI2\QuantGit\trading-research-os.

TASK MODE: Optional future development, not remediation.

Keep the system research-only. Do not enable live trading, futures, leverage, or real orders. Do not add API key forms or real exchange configs.

Goal: Improve v1 usability without changing architecture.

Optional tasks:
1. Add a `--latest-only` or `--run-id` option to `scripts/score_strategies.py` so demo output can avoid printing repeated historical decisions from accumulated database runs.
2. Add a `--clean-demo` or documented temp-database workflow for local demos, while preserving append-only history by default.
3. Optionally harmonize README wording for FinceptTerminal with `configs/engine_registry.yaml` by saying `scaffold_only / future UI inspiration`, without claiming implementation.
4. Do not implement full OpenBB/Qlib/LEAN/Hummingbot/Nautilus/FinceptTerminal integrations in this pass.
5. Run only safe checks: `python -m compileall src scripts -q` and `python -m pytest -q`.

Acceptance:
- No live-trading capability added.
- Existing tests pass.
- Existing append-only behavior remains available.
- Demo scoring output is easier to read when requested.
```
