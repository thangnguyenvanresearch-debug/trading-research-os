# Manual Visual Checklist

Launch from the project root:

```powershell
python -m streamlit run src/dashboard/app.py --server.port 8501 --server.address localhost
```

Open `http://localhost:8501` and press Ctrl+F5.

- [ ] Sidebar shows the Trading Research OS brand and four navigation groups.
- [ ] Research Control Center opens with a hero, safety badges, and six status cards.
- [ ] “What this means” shows healthy, caveat, and future-work panels.
- [ ] Raw Control Center details remain accessible under expanders.
- [ ] Market Cockpit opens without a red error screen.
- [ ] Market Cockpit shows selected market, latest close, coverage, and missing-close cards.
- [ ] Backtest Leaderboard and Risk Gate are summary-first.
- [ ] Local AI unavailable state shows `ollama serve`, `ollama list`, and `qwen2.5:3b`.
- [ ] LEAN says executable unverified.
- [ ] Qlib says dataset export works and trainer is missing.
- [ ] No API key, credential, live-trading, or order controls are visible.

