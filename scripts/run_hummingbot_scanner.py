from __future__ import annotations

import _bootstrap  # noqa: F401

from hummingbot_brain.arbitrage_alert_engine import opportunity_score
from hummingbot_brain.spread_scanner import scan_spread


def main() -> None:
    spread = scan_spread("BTC/USDT", 64990, 65010)
    alert = opportunity_score(spread["gross_spread"], 0.002, 0.0005)
    print({**spread, **alert, "mode": "alert_only"})


if __name__ == "__main__":
    main()
