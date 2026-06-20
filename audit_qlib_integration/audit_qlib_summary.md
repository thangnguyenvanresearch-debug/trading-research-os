# Audit Qlib Integration - Summary

## Verdict

**accepted_with_minor_followups**  
Score: **8.8 / 10**

Qlib integration hiện an toàn để checkpoint. Hệ thống đã có đường research-only để export dataset từ OpenBB local data, ghi DB/report, xử lý Qlib unavailable rõ ràng, và không tạo metric/prediction giả khi Qlib chưa cài.

## Kết quả xác minh

- Qlib installed: `false`
- `python scripts/init_database.py`: passed
- `python -m compileall src scripts -q`: passed
- `python -m compileall src\dashboard -q`: passed
- `python -m pytest -q`: passed, `120 passed`
- Qlib skip-run smoke: passed
- Qlib normal run khi package thiếu: passed với status `unavailable`
- Dataset latest:
  - export_id: `qlib_export_b9c5625b0de2`
  - rows: `2220`
  - columns: `13`
  - symbols: `AAPL`, `MSFT`
  - duplicate `symbol+timestamp`: `0`
  - label column: `label_forward_return_5d`
- Experiment latest:
  - run_id: `qlib_run_045090f920b8`
  - status: `unavailable`
  - metrics_count: `0`
  - predictions_count: `0`

## No-lookahead

No-lookahead cho features được xác minh ở mức source inspection:

- `close_return_1d`: dùng `pct_change(1)`
- `close_return_5d`: dùng `pct_change(5)`
- `momentum_20d`: dùng `pct_change(20)`
- `volatility_20d`: dùng rolling std trên return trailing
- `volume_zscore_20d`: dùng rolling mean/std trailing
- `label_forward_return_5d`: dùng `shift(-horizon)` nhưng chỉ nằm ở label, manifest ghi rõ tách label khỏi feature columns

Không phát hiện feature dùng future data.

## Safety

Không phát hiện:

- OpenAI API integration
- ChatGPT OAuth/cookie/browser automation
- password/credential handling
- cloud credentials
- brokerage/live/order enablement
- futures/leverage
- remote Qlib dataset fetch

## Remaining issues

- True Qlib execution chưa xác minh vì Qlib chưa được cài.
- Dashboard visual/HTTP không verified vì Streamlit không chạy tại `localhost:8501`.
- Nếu Qlib được cài sau này, code hiện chạy pandas baseline research-only chứ chưa phải true Qlib trainer; cần phase riêng để tích hợp trainer thật.

## Checkpoint

An toàn để checkpoint. Qlib hiện ở trạng thái **partial / research-only dataset export**, chưa phải production Qlib experiment engine.
