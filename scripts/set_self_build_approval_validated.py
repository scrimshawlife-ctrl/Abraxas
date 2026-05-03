from __future__ import annotations

from pathlib import Path
import os
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from abraxas.registry.self_build_approval_setter import run_self_build_approval_setter


def _parse_ids(value: str) -> list[str]:
    if not value.strip():
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def main() -> None:
    approved = _parse_ids(os.environ.get("APPROVED_IDS", ""))
    rejected = _parse_ids(os.environ.get("REJECTED_IDS", ""))
    result = run_self_build_approval_setter(approved, rejected)
    print(result)


if __name__ == "__main__":
    main()
