from __future__ import annotations

import hashlib
import json

from abraxas.viz.frontend_provisioning_manifest import build_manifest


def test_manifest_determinism() -> None:
    m1 = build_manifest()
    m2 = build_manifest()
    assert m1["manifest_id"] == m2["manifest_id"]
    assert m1["manifest_hash"] == m2["manifest_hash"]


def test_registry_policy() -> None:
    m = build_manifest()
    assert m["registry_policy"]["registry"] == "https://registry.npmjs.org/"
    assert m["registry_policy"]["credentials_required"] is False


def test_authority_blocking() -> None:
    m = build_manifest()
    authority = m["authority"]
    assert authority["interaction_runtime"] is False
    assert authority["execution"] is False
    assert authority["scheduler"] is False


def test_required_files_exist_flags() -> None:
    m = build_manifest()
    assert "package.json" in m["required_files"]
    assert "package-lock.json" in m["required_files"]
    assert ".npmrc" in m["required_files"]


def test_hash_excludes_self() -> None:
    m = build_manifest()
    temp = dict(m)
    temp.pop("manifest_hash")
    recalculated = hashlib.sha256(
        json.dumps(temp, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    assert recalculated == m["manifest_hash"]
