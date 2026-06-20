from __future__ import annotations

from ai_strategy_brain.strategy_generator import generate_specs
from core.validation import analyze_python_lookahead_risk
from freqtrade_brain.freqtrade_strategy_converter import render_freqtrade_strategy


def test_generated_freqtrade_code_has_no_negative_shift() -> None:
    spec = generate_specs("crypto", 1, ["BTC/USDT"])[0]
    code = render_freqtrade_strategy(spec)
    assert "shift(-" not in code
    assert "can_short = False" in code
    assert "return 1.0" in code


def test_ast_detects_negative_shift_subscript() -> None:
    review = analyze_python_lookahead_risk("signal = df['close'].shift(-1)")
    assert review["has_risk"]
    assert any("negative pandas shift" in pattern for pattern in review["risk_patterns"])


def test_ast_detects_negative_shift_attribute() -> None:
    review = analyze_python_lookahead_risk("signal = df.close.shift(-2)")
    assert review["has_risk"]


def test_ast_detects_keyword_negative_shift() -> None:
    review = analyze_python_lookahead_risk("x = df.close.shift(periods=-1)")
    assert review["has_risk"]
    messages = review["risk_patterns"] + review["warnings"]
    assert any("negative pandas shift" in message or "look-ahead" in message.lower() for message in messages)


def test_ast_detects_future_iloc_offset() -> None:
    review = analyze_python_lookahead_risk("value = dataframe.iloc[i + 1]")
    assert review["has_risk"]
    assert any("future iloc offset" in pattern for pattern in review["risk_patterns"])


def test_ast_detects_future_iloc_variable_offset() -> None:
    review = analyze_python_lookahead_risk("value = dataframe.iloc[index + n]")
    assert review["has_risk"]


def test_ast_detects_future_variable_names() -> None:
    review = analyze_python_lookahead_risk("future_close = close.shift(1)\nnext_candle = 1")
    assert review["has_risk"]
    assert any("future-looking identifier" in pattern for pattern in review["risk_patterns"])


def test_ast_allows_past_only_indicators() -> None:
    review = analyze_python_lookahead_risk(
        "dataframe['ema'] = dataframe['close'].ewm(span=20).mean()\n"
        "dataframe['prev'] = dataframe['close'].shift(1)\n"
        "dataframe['roll'] = dataframe['close'].rolling(20).mean()"
    )
    assert not review["has_risk"]
