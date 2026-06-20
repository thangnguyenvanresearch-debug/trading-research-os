from __future__ import annotations

import subprocess
from pathlib import Path


def main() -> None:
    app = Path(__file__).resolve().parents[1] / "src" / "dashboard" / "streamlit_app.py"
    subprocess.run(["streamlit", "run", str(app)], check=False)


if __name__ == "__main__":
    main()

