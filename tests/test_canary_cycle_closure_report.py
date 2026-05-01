from __future__ import annotations

import copy

from abraxas.canary.closure_runner import run_cycle_closure_report
from abraxas.core.canonical import canonical_json


def _forward_exec(statuses):
    return {"executions": [{"execution_status": s} for s in statuses]}


def _rollback_exec(statuses):
    return {"executions": [{"execution_status": s} for s in statuses]}


def _forward_obs(rows):
    return {"entries": rows}


def _rollback_obs(n):
    return {"observations": [{"id": i} for i in range(n)]}


def test_cycle_closure_states_and_determinism() -> None:
    f_obs_complete = _forward_obs([
        {"rollback": {"rollback_key": "k1"}, "replay": {"replayable": True}},
        {"rollback": {"rollback_key": "k2"}, "replay": {"replayable": True}},
    ])
    out_closed = run_cycle_closure_report(
        forward_observations=f_obs_complete,
        rollback_observations=_rollback_obs(2),
        forward_executions=_forward_exec(["completed", "failed"]),
        rollback_executions=_rollback_exec(["completed", "blocked"]),
    )
    assert out_closed["closure"]["closure_status"] == "closed"
    assert out_closed["symmetry"]["observation_symmetry_status"] == "complete"
    assert out_closed["reversibility"]["reversibility_status"] == "ready"

    out_noexec = run_cycle_closure_report(
        forward_observations=_forward_obs([]),
        rollback_observations=_rollback_obs(0),
        forward_executions=_forward_exec([]),
        rollback_executions=_rollback_exec([]),
    )
    assert out_noexec["closure"]["closure_status"] == "not_computable"

    out_fmiss = run_cycle_closure_report(
        forward_observations=_forward_obs([]),
        rollback_observations=_rollback_obs(1),
        forward_executions=_forward_exec(["completed"]),
        rollback_executions=_rollback_exec(["completed"]),
    )
    assert out_fmiss["symmetry"]["observation_symmetry_status"] == "forward_missing_observations"

    out_rmiss = run_cycle_closure_report(
        forward_observations=_forward_obs([{"rollback": {"rollback_key": None}, "replay": {"replayable": True}}]),
        rollback_observations=_rollback_obs(0),
        forward_executions=_forward_exec(["completed"]),
        rollback_executions=_rollback_exec(["completed"]),
    )
    assert out_rmiss["symmetry"]["observation_symmetry_status"] == "rollback_missing_observations"
    assert out_rmiss["reversibility"]["reversibility_status"] == "partial"

    out_bmiss = run_cycle_closure_report(
        forward_observations=_forward_obs([]),
        rollback_observations=_rollback_obs(0),
        forward_executions=_forward_exec(["completed"]),
        rollback_executions=_rollback_exec(["completed"]),
    )
    assert out_bmiss["symmetry"]["observation_symmetry_status"] == "both_missing_observations"

    # rounding, deterministic ids/hashes, immutability, authority
    f_exec = _forward_exec(["completed", "completed", "failed"])
    f_obs = _forward_obs([{"rollback": {"rollback_key": "k"}, "replay": {"replayable": True}}])
    r_exec = _rollback_exec(["completed", "failed"])
    r_obs = _rollback_obs(1)
    in0 = copy.deepcopy((f_exec, f_obs, r_exec, r_obs))
    out_a = run_cycle_closure_report(f_obs, r_obs, f_exec, r_exec)
    out_b = run_cycle_closure_report(f_obs, r_obs, f_exec, r_exec)
    assert out_a["symmetry"]["forward_observation_coverage"] == 0.333333
    assert out_a["report_id"] == out_b["report_id"]
    assert out_a["report_hash"] == out_b["report_hash"]
    assert canonical_json(out_a) == canonical_json(out_b)
    assert out_a["authority"] == {
        "closure_report_generation": True,
        "production_activation": False,
        "baseline_mutation": False,
        "runtime_config_write": False,
        "promotion": False,
        "execution": False,
        "scheduler": False,
    }
    assert (f_exec, f_obs, r_exec, r_obs) == in0
    assert out_a["counts"]["forward_executions_total"] == 3
