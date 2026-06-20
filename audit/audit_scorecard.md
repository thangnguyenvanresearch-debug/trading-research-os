# Audit scorecard

| Hạng mục | Điểm /10 | Nhận định ngắn |
|---|---:|---|
| Architecture | 6.5 | Tách module đúng ý tưởng multi-brain, nhưng nhiều brain chỉ là stub và có coupling trực tiếp vào database/path globals. |
| Repo leverage | 4.0 | Freqtrade có converter/fallback pipeline; OpenBB/LEAN/Qlib/Hummingbot/Nautilus chủ yếu scaffold. FinceptTerminal chỉ được nhắc trong config/README. |
| Data layer | 6.0 | Có schema, data folders, feature store; ingestion đang dùng sample synthetic mặc định, chưa có import Freqtrade thật hoàn chỉnh. |
| Strategy spec safety | 7.0 | YAML-first, validator có required fields, whitelist indicator/operator, no leverage/futures; look-ahead check còn nông. |
| Backtesting | 4.5 | Có fallback backtester và lưu metrics; Freqtrade CLI wrapper chưa xuất/parse kết quả thật, LEAN/Qlib scaffold. |
| Risk gate | 5.5 | Có reject drawdown/trades/PF/OOS/cost/concentration/smoothness; thiếu dry-run divergence, look-ahead runtime checks, archived/approved_for_dry_run path. |
| Decision engine | 5.0 | Có score 0-100 và permission v1; hardcode symbol BTC/USDT, lý do còn chung chung, không match regime thật theo strategy/spec. |
| Dashboard | 6.0 | Có đủ 9 page và cockpit cơ bản; nhiều page chỉ hiển thị placeholder/bảng, thiếu readiness và engine warning chi tiết. |
| Security | 7.0 | Không thấy secret pattern; live/futures/leverage mặc định tắt; thiếu `.gitignore`, generated data/db hiện diện trong workspace. |
| Code quality | 5.5 | Module nhỏ, type hints tương đối; còn silent/broad exception, dead imports, duplicate indicator code, hardcoded workflow assumptions. |
| Testing | 4.5 | Có 5 test cơ bản; thiếu integration tests, optional engine graceful tests, safe defaults tests, parser tests. |
| Documentation | 7.0 | README rõ mục đích, setup, safety, limitation; chưa nêu đủ trạng thái scaffold-only từng engine. |
| Retail-user practicality | 5.5 | Dễ chạy demo local với sample data; chưa đủ tin cậy cho người dùng retail dùng nghiên cứu thật nếu chưa tích hợp data/backtest engine thật. |

**Overall score:** 5.8 / 10

