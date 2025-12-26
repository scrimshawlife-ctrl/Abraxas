from __future__ import annotations

import json
from pathlib import Path

from abraxas.evolve.ledger import append_epp_ledger


def test_epp_ledger_chain(tmp_path):
    ledger_path = tmp_path / "value_ledgers" / "epp_runs.jsonl"
    pack_a = {
        "pack_id": "epp_a",
        "run_id": "run123",
        "proposals": [{"proposal_id": "p1"}],
        "summary": {"proposal_count": 1},
    }
    pack_b = {
        "pack_id": "epp_b",
        "run_id": "run123",
        "proposals": [{"proposal_id": "p2"}],
        "summary": {"proposal_count": 1},
    }

    append_epp_ledger(pack_a, ledger_path=ledger_path)
    append_epp_ledger(pack_b, ledger_path=ledger_path)

    lines = ledger_path.read_text().splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    second = json.loads(lines[1])
    assert second["prev_hash"] == first["step_hash"]
