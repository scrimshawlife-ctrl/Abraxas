from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from abraxas.registry import load_subsystem_registry


def main() -> None:
    result = load_subsystem_registry()
    output = {
        "schema_version": "SubsystemRegistryLoadRun.v1",
        "registry_path": result.registry_path,
        "registry_id": result.registry_id,
        "subsystem_count": result.subsystem_count,
        "subsystem_ids": list(result.subsystem_ids),
        "canonical_hash": result.canonical_hash,
        "authority": {
            "mutation": False,
            "promotion": False,
            "execution": False,
            "observe_only": True,
        },
    }

    out_path = Path("out/registry/subsystem_registry_load.latest.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(output, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
