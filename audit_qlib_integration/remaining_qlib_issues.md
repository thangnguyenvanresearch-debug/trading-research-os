# Remaining Qlib Issues

## Critical / High / Medium

Không phát hiện critical, high, hoặc medium issue.

## Low

1. **True Qlib execution chưa verified**

- Evidence: `qlib_installed=False`.
- Impact: Chưa thể claim Qlib trainer/model/prediction pipeline hoạt động thật.
- Action: Cài Qlib trong phase riêng, chạy local-only experiment không remote dataset/cloud.

2. **Future Qlib-installed branch đang là pandas baseline**

- Evidence: `src/qlib_brain/qlib_runner.py` chạy `fallback_baseline_experiment()` khi Qlib import được.
- Impact: Có thể gây nhầm nếu người dùng kỳ vọng true Qlib training. Dù model name có `pandas_baseline_research_only`, vẫn lưu vào `qlib_predictions`.
- Action: Khi triển khai Qlib thật, tách baseline sang bảng/section riêng hoặc thay bằng real Qlib trainer output.

3. **Dashboard visual chưa verified**

- Evidence: HTTP check `localhost:8501` bị refused vì Streamlit không chạy.
- Impact: Chưa xác minh UI trực quan page 15.
- Action: Start Streamlit và kiểm page `15_qlib_research` thủ công.

4. **Tests chưa kiểm thủ công mọi rolling feature**

- Evidence: test kiểm label separation và 1-day return, nhưng chưa assert từng công thức rolling.
- Impact: Rủi ro thấp vì source formula đơn giản và đã inspect.
- Action: Thêm fixture nhỏ cho `close_return_5d`, `momentum_20d`, `volatility_20d`, `volume_zscore_20d`.
