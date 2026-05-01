from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict

from abraxas.core.canonical import canonical_json, sha256_hex


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_manifest(frontend_root: Path) -> Dict[str, object]:
    files = ["package.json", "package-lock.json", "vitest.config.ts", "tsconfig.json"]
    contents: Dict[str, str] = {}
    for rel in files:
        contents[rel] = sha256_bytes((frontend_root / rel).read_bytes())

    payload: Dict[str, object] = {
        "type": "AALVizFrontendHarnessManifest.v1",
        "files": contents,
    }
    manifest_id = sha256_hex(canonical_json(payload))
    payload["manifest_id"] = manifest_id
    payload["manifest_hash"] = sha256_hex(canonical_json(payload))
    return payload
