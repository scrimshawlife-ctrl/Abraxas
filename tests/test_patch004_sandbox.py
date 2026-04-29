from abx.repair.noop_executor import run_noop_executor
from abx.repair.planner import build_repair_manifest


def _summary(**kwargs):
    base = {
        "readiness_status": "READY_FOR_DESIGN",
        "design_pass_allowed": True,
        "execution_allowed": False,
        "runtime_mutation_allowed": False,
        "execution_triggered": False,
        "runtime_mutation": False,
        "authority_leak_detected": False,
        "cycle_count_observed": 30,
    }
    base.update(kwargs)
    return base


def test_ready_for_design_zero_execution():
    m = build_repair_manifest(_summary())
    r = run_noop_executor(m)
    assert r["status"] == "PASS"
    assert r["actions_executed"] == 0


def test_execution_allowed_blocks():
    r = run_noop_executor(build_repair_manifest(_summary(execution_allowed=True)))
    assert r["status"] == "BLOCKED"


def test_runtime_mutation_allowed_blocks():
    r = run_noop_executor(build_repair_manifest(_summary(runtime_mutation_allowed=True)))
    assert r["status"] == "BLOCKED"


def test_hard_blocked_blocks():
    r = run_noop_executor(build_repair_manifest(_summary(readiness_status="HARD_BLOCKED")))
    assert r["status"] == "NOT_COMPUTABLE"


def test_not_computable_blocks():
    r = run_noop_executor(build_repair_manifest(_summary(readiness_status="NOT_COMPUTABLE")))
    assert r["status"] == "NOT_COMPUTABLE"


def test_receipt_no_mutation_flags():
    r = run_noop_executor(build_repair_manifest(_summary()))
    assert r["files_modified"] == []
    assert r["actions_executed"] == 0
    assert r["execution_triggered"] is False
    assert r["runtime_mutation"] is False
    assert r["authority_leak_detected"] is False
    assert r["sandbox_only"] is True
    assert r["patch_004_execution_allowed"] is False
