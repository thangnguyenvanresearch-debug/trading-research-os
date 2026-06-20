from __future__ import annotations


def build_reasons(strategy_name: str, regime: str, score: int) -> list[str]:
    return [
        f"{strategy_name} has a current research score of {score}.",
        f"Latest detected regime is {regime or 'unknown'}.",
        "Strategy passed through YAML validation and controlled conversion.",
        "Backtest evidence is research-only and not proof of future profit.",
    ]

