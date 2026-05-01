from __future__ import annotations

import copy
from pathlib import Path

from abraxas.canary.rollback_execution_runner import run_rollback_executor
from abraxas.core.canonical import canonical_json


def _packet(**overrides):
    base = {
        "packet_id": "p1",
        "rollback_id": "rb1",
        "observation_id": "ob1",
        "execution_id": "src1",
        "source_key": "s1",
        "packet_status": "pending_review",
        "recommendation_status": "recommend_approve_for_rollback_review",
        "rollback_plan": {"mode": "deterministic_replay", "requires_artifact": True, "artifact_hash": "ah", "artifact_path": "/tmp/a"},
        "authority": {
            "rollback_packet_generation": True,
            "rollback_execution": False,
            "production_activation": False,
            "baseline_mutation": False,
            "runtime_config_write": False,
            "promotion": False,
            "execution": False,
            "scheduler": False,
        },
    }
    base.update(overrides)
    return base


def test_rollback_executor_modes_rules_determinism_counts_ordering_authority_immutability(tmp_path: Path, monkeypatch) -> None:
    p_ok = _packet(packet_id="p1", source_key="s1")
    p_non_pending = _packet(packet_id="p2", source_key="s2", packet_status="done")
    p_non_approved = _packet(packet_id="p3", source_key="s3", recommendation_status="recommend_hold")
    p_blocked = _packet(packet_id="p4", source_key="s4")
    p_blocked["authority"]["promotion"] = True

    run_in = {"packets": [p_non_approved, p_ok, p_non_pending, p_blocked]}
    run0 = copy.deepcopy(run_in)

    out_mem = run_rollback_executor(run_in, created_at="2026-01-01T00:00:00Z", scope_id="scopeA")
    ex_by_src = {e["source_key"]: e for e in out_mem["executions"]}
    assert ex_by_src["s1"]["execution_status"] == "completed"
    assert ex_by_src["s1"]["mode"] == "in_memory"
    assert ex_by_src["s1"]["artifact"]["artifact_hash"] is not None
    assert ex_by_src["s1"]["artifact"]["artifact_path"] is None
    assert ex_by_src["s2"]["execution_status"] == "skipped"
    assert ex_by_src["s3"]["execution_status"] == "skipped"
    assert ex_by_src["s4"]["execution_status"] == "blocked"
    assert ex_by_src["s4"]["failure"]["reason"].startswith("forbidden_authority_signal:")

    assert out_mem["authority"] == {
        "rollback_execution": True,
        "sandbox_only": True,
        "production_activation": False,
        "baseline_mutation": False,
        "runtime_config_write": False,
        "promotion": False,
        "execution": False,
        "scheduler": False,
    }
    assert out_mem["counts"] == {"packets_total": 4, "completed": 1, "skipped": 2, "blocked": 1, "failed": 0}
    assert out_mem["executions"] == sorted(out_mem["executions"], key=lambda e: (e["source_key"], e["execution_id"]))
    assert run_in == run0

    # execution_id excludes created_at
    out_mem_2 = run_rollback_executor(run_in, created_at="2099-01-01T00:00:00Z", scope_id="scopeA")
    assert {e["packet_id"]: e["execution_id"] for e in out_mem["executions"]} == {e["packet_id"]: e["execution_id"] for e in out_mem_2["executions"]}

    # sandbox mode writes receipt
    out_sb = run_rollback_executor({"packets": [_packet()]}, created_at="2026-01-01T00:00:00Z", scope_id="scopeA", sandbox_root=str(tmp_path / "sb"))
    ex = out_sb["executions"][0]
    rp = Path(ex["scope"]["receipt_path"])
    assert rp.exists()
    assert (tmp_path / "sb") in rp.parents

    # path escape blocked
    from pathlib import Path as P
    orig_resolve = P.resolve

    def fake_resolve(self: P, *a, **k):
        if self.name.endswith('.json'):
            return P('/tmp/escaped.json')
        return orig_resolve(self, *a, **k)

    monkeypatch.setattr(P, 'resolve', fake_resolve)
    out_escape = run_rollback_executor({"packets": [_packet()]}, created_at="2026-01-01T00:00:00Z", scope_id="scopeA", sandbox_root=str(tmp_path / "sb2"))
    assert out_escape["executions"][0]["execution_status"] == "blocked"
    assert out_escape["executions"][0]["failure"]["reason"] == "sandbox_path_escape"

    monkeypatch.setattr(P, 'resolve', orig_resolve)
    # sandbox write failure
    def bad_write(*_a, **_k):
        raise OSError("x")

    monkeypatch.setattr(Path, 'write_text', bad_write)
    out_fail = run_rollback_executor({"packets": [_packet()]}, created_at="2026-01-01T00:00:00Z", scope_id="scopeA", sandbox_root=str(tmp_path / "sb3"))
    assert out_fail["executions"][0]["execution_status"] == "failed"
    assert out_fail["executions"][0]["failure"]["reason"] == "sandbox_write_failed"

    # deterministic bytes with same controls
    out_a = run_rollback_executor({"packets": [_packet()]}, created_at="2026-01-01T00:00:00Z", scope_id="scopeA")
    out_b = run_rollback_executor({"packets": [_packet()]}, created_at="2026-01-01T00:00:00Z", scope_id="scopeA")
    assert canonical_json(out_a) == canonical_json(out_b)
