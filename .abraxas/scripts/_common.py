#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ABRAXAS = ROOT / ".abraxas"


def load_yaml(path: Path) -> Any:
    return json.loads(path.read_text())


def dump_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_subsystem(subsystem_id: str) -> dict[str, Any]:
    path = ABRAXAS / "subsystems" / f"{subsystem_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Unknown subsystem: {subsystem_id}")
    return load_yaml(path)


def subsystem_ids() -> list[str]:
    reg = load_yaml(ABRAXAS / "registries" / "expected_subsystems.yaml")
    return list(reg.get("subsystems", []))


def parser_base(description: str) -> argparse.ArgumentParser:
    return argparse.ArgumentParser(description=description)
