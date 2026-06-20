from __future__ import annotations

import _bootstrap  # noqa: F401

from feature_brain.feature_pipeline import build_features


def main() -> None:
    features = build_features()
    print(f"Built {len(features)} feature rows.")


if __name__ == "__main__":
    main()

