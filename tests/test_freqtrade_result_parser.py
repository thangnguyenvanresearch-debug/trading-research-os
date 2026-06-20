from __future__ import annotations

import json

from freqtrade_brain.freqtrade_result_parser import parse_freqtrade_result


def test_parse_freqtrade_strategy_export(tmp_path) -> None:
    path = tmp_path / "result.json"
    path.write_text(
        json.dumps(
            {
                "strategy": {
                    "ExampleStrategy": {
                        "profit_total": 0.12,
                        "max_drawdown": 0.08,
                        "winrate": 0.55,
                        "total_trades": 120,
                        "profit_factor": 1.4,
                        "sharpe": 1.2,
                        "sortino": 1.5,
                        "profit_mean": 0.002,
                        "results_per_pair": [
                            {"key": "BTC/USDT", "profit_total": 0.10, "total_trades": 70},
                            {"key": "ETH/USDT", "profit_total": -0.02, "total_trades": 50},
                        ],
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    parsed = parse_freqtrade_result(path, "ExampleStrategy")
    assert parsed["total_return"] == 0.12
    assert parsed["max_drawdown"] == 0.08
    assert parsed["win_rate"] == 0.55
    assert parsed["trade_count"] == 120
    assert parsed["profit_factor"] == 1.4
    assert parsed["best_pair"] == "BTC/USDT"
    assert parsed["worst_pair"] == "ETH/USDT"


def test_parse_freqtrade_missing_fields_warns(tmp_path) -> None:
    path = tmp_path / "minimal.json"
    path.write_text(json.dumps({"strategy": {"ExampleStrategy": {"total_trades": 1}}}), encoding="utf-8")
    parsed = parse_freqtrade_result(path, "ExampleStrategy")
    assert parsed["trade_count"] == 1
    assert parsed["parser_warnings"]

