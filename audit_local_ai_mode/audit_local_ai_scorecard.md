# Scorecard Local AI Mode

| Hạng mục | Điểm / 10 | Nhận xét |
|---|---:|---|
| Safety invariants | 9.7 | Không phát hiện OpenAI API, ChatGPT OAuth, cookie, browser automation, order/live enablement. |
| Local AI config | 9.2 | Safe defaults tốt; `allow_external_api` nên được enforce rõ hơn nếu `safe_mode` bị tắt. |
| Database schema | 9.2 | `ai_research_memos` đầy đủ, SQLite verified, DuckDB likely but not runtime verified. |
| Local AI client | 9.1 | Ollama local endpoint, timeout, `stream=false`, structured errors. |
| Research context/prompt | 9.0 | Đọc DB local, prompt an toàn; `_safe_fetch` hơi rộng. |
| CLI usability | 9.2 | Graceful unavailable path, output rõ. |
| Dashboard safety | 9.0 | Không có order/API key controls; page load có local health check có thể delay. |
| Tests | 9.3 | 58 tests pass, coverage tốt cho mock/unavailable paths. |
| Regression safety | 9.4 | Freqtrade/sample workflow pass. |
| Documentation | 9.1 | README giải thích rõ Local AI/Ollama và không dùng OpenAI/ChatGPT backend. |
| Retail-user practicality | 8.8 | Dễ chạy nếu có Ollama; cần hướng dẫn troubleshoot model chưa pull/endpoint unavailable sâu hơn. |
| Overall readiness | 9.1 | Accepted with minor followups. |
