from __future__ import annotations

import json
import os
import tempfile

from abraxas.oracle.v2.bridge import main


def test_bridge_forwards_evidence_flags_and_still_succeeds_when_missing():
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
            "--config-hash", "FIXED_CONFIG_HASH_0000000000000000",
            "--v1-cmd", v1_cmd,
            "--v1-out-dir", out,
            "--out-dir", out,
            "--no-ledger",
            "--evidence", "news=news.json",
        ])
        assert rc == 0
        assert os.path.exists(os.path.join(out, "latest", "surface.json"))
        assert os.path.exists(os.path.join(out, "latest", "manifest.json"))
