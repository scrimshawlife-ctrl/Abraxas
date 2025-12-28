from __future__ import annotations

import json
import os
import tempfile

from abraxas.oracle.v2.bridge import main


def test_bridge_runs_v2_when_v1_cmd_succeeds():
    """
    We simulate a v1 command by writing out/latest/envelope.json via python -c.
    """
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "out")
        latest = os.path.join(out, "latest")
        os.makedirs(latest, exist_ok=True)

        env_path = os.path.join(latest, "envelope.json")
        v1_cmd = (
            'python -c "import json,os;'
            f'os.makedirs({latest!r},exist_ok=True);'
            f'json.dump({{\'oracle_signal\':{{\'scores_v1\':{{\'slang\':{{\'top_risk\':[]}},\'aalmanac\':{{\'top_patterns\':[]}}}}}}}}, open({env_path!r}, \'w\'))"'
        )
        rc = main([
            "--config-hash", "CFG",
            "--v1-cmd", v1_cmd,
            "--v1-out-dir", out,
            "--out-dir", out,
            "--no-ledger",
        ])
        assert rc == 0
        # v2 should have created run artifacts
        runs = [d for d in os.listdir(out) if d != "latest"]
        assert len(runs) >= 1
