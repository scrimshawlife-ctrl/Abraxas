from __future__ import annotations

import os
import tempfile

from abraxas.oracle.v2.config import default_config, config_hash, write_config, load_or_create_config


def test_config_hash_deterministic():
    cfg = default_config(profile="default", bw_high=20.0, mrs_high=70.0, ledger_enabled=True)
    a = config_hash(cfg)
    b = config_hash(cfg)
    assert a == b
    assert len(a) == 64


def test_load_or_create_writes_files():
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "oracle_v2_config.json")
        cfg, h = load_or_create_config(path=path, profile="default", bw_high=20.0, mrs_high=70.0, ledger_enabled=True)
        assert os.path.exists(path)
        assert os.path.exists(path + ".hash")
        assert len(h) == 64
