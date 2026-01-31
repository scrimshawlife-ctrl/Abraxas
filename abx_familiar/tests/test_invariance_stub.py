from abx_familiar.governance.invariance_gate import invariance_gate
from abx_familiar.runtime.familiar_runtime import FamiliarRuntime


def test_invariance_gate_stub_fails_when_disabled():
    result = invariance_gate({})
    assert result["passed"] is False
    assert result["reason"] == "stub_not_implemented"


def test_invariance_gate_reports_missing_runtime_or_context_when_enabled():
    result = invariance_gate({}, enabled=True)
    assert result["passed"] is False
    assert result["reason"] == "missing_runtime_or_context"


def test_invariance_gate_can_run_harness_when_enabled():
    rt = FamiliarRuntime()
    ctx = {
        "run_id": "r_gate",
        "summoner": {
            "task_id": "t_ok",
            "tier_scope": "Academic",
            "mode": "Analyst",
            "requested_ops": [],
            "constraints": {"x": 1},
        },
    }
    result = invariance_gate({}, enabled=True, runtime=rt, context=ctx, runs_required=3)
    assert "passed" in result
    assert "reason" in result
