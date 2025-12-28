from __future__ import annotations

import json
import os
import tempfile

from abraxas.oracle.v2.cli import main


def test_cli_evidence_flag_does_not_fail_when_missing():
    with tempfile.TemporaryDirectory() as td:
        rc = main([
            "--config-hash", "FIXED_CONFIG_HASH_0000000000000000",
            "--out-dir", td,
            "--no-ledger",
            "--evidence", "news=news.json",
        ])
        assert rc == 0
        # latest outputs still exist
        latest = os.path.join(td, "latest")
        assert os.path.exists(os.path.join(latest, "surface.json"))
        assert os.path.exists(os.path.join(latest, "envelope.json"))
        assert os.path.exists(os.path.join(latest, "manifest.json"))
