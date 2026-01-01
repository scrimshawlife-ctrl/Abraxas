from __future__ import annotations

import json
import os


def _read_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_schema_v2_index_paths_exist():
    idx_path = os.path.join("schema", "v2", "index.json")
    assert os.path.exists(idx_path), "schema/v2/index.json missing"

    idx = _read_json(idx_path)
    v2 = idx.get("v2")
    assert isinstance(v2, dict), "schema/v2/index.json must contain object at key 'v2'"
    assert len(v2) >= 1, "schema/v2/index.json has empty registry"

    for k, rel in v2.items():
        assert isinstance(k, str) and k.strip(), f"empty key in schema index: {k!r}"
        assert isinstance(rel, str) and rel.strip(), f"empty path for key {k!r}"
        # Paths are recorded as repo-relative paths in index.json
        assert os.path.exists(rel), f"schema index entry missing file: {k} -> {rel}"


def test_schema_v2_id_matches_path_when_present():
    """
    If a schema file contains $id, it should match its on-disk path (best-effort).
    If $id missing, do not fail.
    """
    idx_path = os.path.join("schema", "v2", "index.json")
    idx = _read_json(idx_path)
    v2 = idx.get("v2", {})
    for k, rel in v2.items():
        schema = _read_json(rel)
        sid = schema.get("$id")
        if isinstance(sid, str) and sid.strip():
            assert sid == rel, f"$id mismatch for {k}: expected {rel}, got {sid}"
