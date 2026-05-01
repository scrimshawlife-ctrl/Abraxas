from __future__ import annotations

import copy

from abraxas.canary.rollback_observation_runner import run_rollback_observation_ledger
from abraxas.core.canonical import canonical_json


def _ex(status: str = "completed", source_key: str = "s1", mode: str = "in_memory") -> dict:
    return {
        "execution_id": f"e-{source_key}",
        "packet_id": f"p-{source_key}",
        "rollback_id": f"r-{source_key}",
        "execution_source_id": f"src-{source_key}",
        "source_key": source_key,
        "execution_status": status,
        "mode": mode,
        "artifact": {"artifact_hash": f"ah-{source_key}", "artifact_path": None if mode == "in_memory" else f"/tmp/{source_key}.json"},
        "scope": {"scope_id": "scope1", "sandbox_root": None if mode == "in_memory" else "/tmp"},
        "lineage": {"execution_hash": f"eh-{source_key}", "rollback_packet_hash": f"ph-{source_key}"},
    }


def test_rollback_observation_ledger_creation_dedupe_determinism_and_counts() -> None:
    inp = {"executions": [_ex("completed", "s2"), _ex("failed", "s1", "sandbox")]}
    inp0 = copy.deepcopy(inp)

    out = run_rollback_observation_ledger(inp)
    assert out["counts"] == {"executions_total": 2, "observations_created": 2, "observations_existing": 0, "observations_total": 2}
    assert out["observations"] == sorted(out["observations"], key=lambda o: (o["source_key"], o["observation_id"]))

    by_src = {o["source_key"]: o for o in out["observations"]}
    assert by_src["s2"]["replay"]["replayable"] is True
    assert by_src["s2"]["rollback"]["rollback_key"] == "ah-s2"
    assert by_src["s1"]["replay"]["replayable"] is False
    assert by_src["s1"]["rollback"]["rollback_key"] is None

    assert out["authority"] == {
        "rollback_observation_ledger_write": True,
        "rollback_execution": False,
        "production_activation": False,
        "baseline_mutation": False,
        "runtime_config_write": False,
        "promotion": False,
        "execution": False,
        "scheduler": False,
    }

    out2 = run_rollback_observation_ledger(inp)
    assert canonical_json(out) == canonical_json(out2)
    assert inp == inp0

    out3 = run_rollback_observation_ledger(inp, out)
    assert out3["counts"]["observations_created"] == 0
    assert out3["counts"]["observations_existing"] == 2
    assert out3["counts"]["observations_total"] == 2
