from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    payload = {
        "schema_version": "SelfBuildApprovalInput.v1",
        "approved_ids": [],
        "rejected_ids": [],
    }
    out_path = Path("out/registry/self_build_approval_input.latest.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
