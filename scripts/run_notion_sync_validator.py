from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from abraxas.registry.notion_sync_validator import run_notion_sync_validator


def main() -> None:
    result = run_notion_sync_validator()
    out_path = Path("out/registry/notion_sync_validator.latest.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
