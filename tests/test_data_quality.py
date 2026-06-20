from __future__ import annotations

from data_brain.data_quality_checks import validate_ohlcv
from data_brain.freqtrade_data_adapter import generate_sample_ohlcv


def test_sample_data_passes_quality_checks() -> None:
    df = generate_sample_ohlcv("BTC/USDT", candles=50)
    assert validate_ohlcv(df) == []
