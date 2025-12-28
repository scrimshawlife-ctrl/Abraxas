from __future__ import annotations

import json
import os
import tempfile

from abraxas.oracle.v2.config import default_config, config_hash, load_or_create_config


def test_default_config_includes_schema_index_payload():
    cfg = default_config(schema_index_path="schema/v2/index.json")
    assert "schema_index" in cfg
    assert "v2" in cfg["schema_index"]


def test_config_hash_changes_when_schema_index_changes():
    with tempfile.TemporaryDirectory() as td:
        idx_path = os.path.join(td, "index.json")
        with open(idx_path, "w", encoding="utf-8") as f:
            json.dump({"v2": {"a": "x"}}, f, sort_keys=True, separators=(",", ":"))
        cfg1 = default_config(schema_index_path=idx_path)
        h1 = config_hash(cfg1)

        with open(idx_path, "w", encoding="utf-8") as f:
            json.dump({"v2": {"a": "x", "b": "y"}}, f, sort_keys=True, separators=(",", ":"))
        cfg2 = default_config(schema_index_path=idx_path)
        h2 = config_hash(cfg2)

        assert h1 != h2


def test_load_or_create_respects_schema_index_path():
    with tempfile.TemporaryDirectory() as td:
        cfg_path = os.path.join(td, "oracle_v2_config.json")
        idx_path = os.path.join(td, "index.json")
        with open(idx_path, "w", encoding="utf-8") as f:
            json.dump({"v2": {"common": "schema/v2/common.json"}}, f, sort_keys=True, separators=(",", ":"))
        cfg, h = load_or_create_config(path=cfg_path, schema_index_path=idx_path)
        assert cfg["schema_index_path"] == idx_path
        assert "common" in cfg["schema_index"]["v2"]
        assert len(h) == 64
