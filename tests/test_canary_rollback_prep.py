from __future__ import annotations

import copy

from abraxas.canary.rollback_runner import run_rollback_prep
from abraxas.core.canonical import canonical_json


def _obs(status: str = "completed", replayable: bool = True, rollback_key: str | None = "rk", source_key: str = "s1") -> dict:
    return {
        "observation_id": "o1",
        "execution_id": "e1",
        "source_key": source_key,
        "execution_status": status,
        "artifact": {"artifact_hash": "ah", "artifact_path": "/tmp/a"},
        "execution": {"created_at": "2026-01-01T00:00:00Z", "mode": "sandbox", "failure_reason": None, "blocked_reason": None},
        "replay": {"replayable": replayable, "replay_key": "rpk"},
        "rollback": {"rollback_prepared": False, "rollback_key": rollback_key},
        "lineage": {"execution_hash": "exh"},
    }


def _run(entries: list[dict]) -> dict:
    return {"entries": entries}


def test_rules_determinism_ordering_authority_immutability_and_counts() -> None:
    a = _obs(status="completed", replayable=True, rollback_key="rk", source_key="s2")
    b = _obs(status="failed", replayable=True, rollback_key="rk", source_key="s1")
    c = _obs(status="completed", replayable=False, rollback_key="rk", source_key="s3")
    d = _obs(status="completed", replayable=True, rollback_key=None, source_key="s4")
    inp = _run([a, b, c, d])
    inp0 = copy.deepcopy(inp)

    out = run_rollback_prep(inp)
    assert out["counts"] == {"observations_total": 4, "prepared": 1, "not_computable": 3}

    by_src = {r["source_key"]: r for r in out["rollbacks"]}
    assert by_src["s2"]["status"] == "prepared"
    assert by_src["s1"]["safety"]["reason"] == "execution_not_completed"
    assert by_src["s3"]["safety"]["reason"] == "not_replayable"
    assert by_src["s4"]["safety"]["reason"] == "missing_rollback_key"

    assert out["rollbacks"] == sorted(out["rollbacks"], key=lambda r: (r["source_key"], r["rollback_id"]))

    assert out["authority"] == {
        "rollback_preparation": True,
        "rollback_execution": False,
        "production_activation": False,
        "baseline_mutation": False,
        "runtime_config_write": False,
        "promotion": False,
        "execution": False,
        "scheduler": False,
    }
    assert inp == inp0

    out2 = run_rollback_prep(inp)
    assert canonical_json(out) == canonical_json(out2)
    assert by_src["s2"]["rollback_id"] == [r for r in out2["rollbacks"] if r["source_key"] == "s2"][0]["rollback_id"]
