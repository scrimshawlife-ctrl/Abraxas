#!/usr/bin/env python3
"""Run rune registry listing.

Prints a summary of the rune catalog available for shadow execution,
including each rune's schema signatures and route nodes.
"""
from __future__ import annotations

import json
import sys
from hashlib import sha256
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Default rune catalog for v2.0.1-rune-layer
RUNE_CATALOG = {
    "RUNE_AUDIT": {
        "input_schema": {"type": "object", "description": "Audit payload"},
        "output_schema": {"type": "object", "description": "Audit result"},
        "route_node": "node.audit",
        "lane": "shadow",
        "version": "1.0.0",
    },
    "RUNE_HASH": {
        "input_schema": {"type": "object", "description": "Hash payload"},
        "output_schema": {"type": "object", "description": "Hash result"},
        "route_node": "node.hash",
        "lane": "shadow",
        "version": "1.0.0",
    },
    "RUNE_VALIDATE": {
        "input_schema": {"type": "object", "description": "Validation payload"},
        "output_schema": {"type": "object", "description": "Validation result"},
        "route_node": "node.validate",
        "lane": "shadow",
        "version": "1.0.0",
    },
    "RUNE_ROUTE": {
        "input_schema": {"type": "object", "description": "Route payload"},
        "output_schema": {"type": "object", "description": "Route result"},
        "route_node": "node.route",
        "lane": "shadow",
        "version": "1.0.0",
    },
}


def build_registry_index(catalog: dict) -> dict:
    """Build a deterministic registry index from the rune catalog."""
    runes = []
    for rune_id, spec in sorted(catalog.items()):
        runes.append({
            "rune_id": rune_id,
            "route_node": spec.get("route_node", ""),
            "lane": spec.get("lane", "shadow"),
            "version": spec.get("version", ""),
        })

    canonical = json.dumps({"runes": runes}, sort_keys=True).encode("utf-8")
    registry_hash = sha256(canonical).hexdigest()

    return {
        "schema_version": "RuneRegistry.v1",
        "rune_count": len(runes),
        "registry_hash": registry_hash,
        "runes": runes,
    }


def main():
    out_dir = Path("out/registry")
    out_dir.mkdir(parents=True, exist_ok=True)

    index = build_registry_index(RUNE_CATALOG)

    out_path = out_dir / "rune_registry.latest.json"
    out_path.write_text(json.dumps(index, indent=2), encoding="utf-8")

    print(f"Rune registry: {index['rune_count']} rune(s) indexed")
    print(f"  Registry hash: {index['registry_hash'][:16]}...")
    for rune in index["runes"]:
        print(f"  [{rune['rune_id']}] route={rune['route_node']} lane={rune['lane']}")
    print(f"  out/registry/rune_registry.latest.json")


if __name__ == "__main__":
    main()
