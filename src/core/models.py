from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class StrategyStatus(StrEnum):
    REJECTED = "rejected"
    WATCHLIST = "watchlist"
    PAPER_ONLY = "paper_only"
    APPROVED_FOR_DRY_RUN = "approved_for_dry_run"
    ARCHIVED = "archived"


class Signal(StrEnum):
    LONG_CANDIDATE = "LONG_CANDIDATE"
    EXIT_CANDIDATE = "EXIT_CANDIDATE"
    WAIT = "WAIT"
    AVOID = "AVOID"


class Permission(StrEnum):
    REJECTED = "REJECTED"
    WATCHLIST = "WATCHLIST"
    PAPER_ONLY = "PAPER_ONLY"
    APPROVED_FOR_DRY_RUN = "APPROVED_FOR_DRY_RUN"


@dataclass(frozen=True)
class StrategySpec:
    strategy_name: str
    asset_class: str
    engine_target: str
    timeframe: str
    pairs: list[str]
    strategy_type: str
    regime_fit: list[str]
    entry_logic: dict[str, Any]
    exit_logic: dict[str, Any]
    risk: dict[str, Any]
    validation: dict[str, Any]
    rationale: str = ""
    rejection_criteria: list[str] = field(default_factory=list)

    @property
    def strategy_id(self) -> str:
        return self.strategy_name.lower().replace(" ", "_")


@dataclass(frozen=True)
class BacktestMetrics:
    strategy_id: str
    run_id: str
    total_return: float
    out_of_sample_return: float
    max_drawdown: float
    sharpe: float | None
    sortino: float | None
    win_rate: float
    trade_count: int
    profit_factor: float
    avg_win: float
    avg_loss: float
    fee_slippage_adjusted_return: float
    pair_concentration: float
    regime_count: int
    equity_smoothness: float

