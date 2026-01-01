from __future__ import annotations

import json
import os
import tempfile

from abraxas.oracle.v2.discover import discover_envelope


def test_discover_envelope_finds_out_latest():
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "out")
        latest = os.path.join(out, "latest")
        os.makedirs(latest, exist_ok=True)
        env_path = os.path.join(latest, "envelope.json")
        with open(env_path, "w", encoding="utf-8") as f:
            json.dump({"oracle_signal": {"scores_v1": {"x": 1}}}, f)

        p, env = discover_envelope(v1_out_dir=out)
        assert p is not None
        assert env is not None
        assert env["oracle_signal"]["scores_v1"]["x"] == 1


def test_discover_envelope_returns_none_when_missing():
    with tempfile.TemporaryDirectory() as td:
        p, env = discover_envelope(v1_out_dir=os.path.join(td, "missing"))
        assert p is None
        assert env is None
