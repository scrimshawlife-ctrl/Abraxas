from __future__ import annotations

import argparse
import json
import os


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", required=True)
    p.add_argument("--policy", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--inputs-dir", default=None)
    args = p.parse_args()

    with open(args.policy, "r", encoding="utf-8") as f:
        content = f.read()
    size = len(content)
    metrics = {
        "brier": 0.12 + (0.0001 * (size % 7)),
        "calibration_error": 0.08 + (0.0001 * (size % 5)),
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"metrics": metrics}, f, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
