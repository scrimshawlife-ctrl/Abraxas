from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    output = {
        "schema_version": "StubRun.v1",
        "status": "NOT_COMPUTABLE",
        "reason": "STUB_SCRIPT",
        "authority": {
            "mutation": False,
            "promotion": False,
            "execution": False,
            "observe_only": True,
        },
    }
    out_path = Path("out/stubs/run_oracle_router.latest.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(output, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
