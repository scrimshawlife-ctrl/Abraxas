from __future__ import annotations

from abraxas.registry.self_build_approval_setter import run_self_build_approval_setter
from abraxas.registry.self_build_batch_cycle import run_self_build_batch_cycle
from abraxas.registry.self_build_operator_queue import run_self_build_operator_queue


def test_batch_waiting_for_approval() -> None:
    run_self_build_approval_setter([], [])
    result = run_self_build_batch_cycle()
    assert result["status"] in {"WAITING_FOR_APPROVAL", "STOPPED_PREFLIGHT_NOT_GREEN"}


def test_batch_apply_or_stops_closed() -> None:
    queue = run_self_build_operator_queue()
    if not queue["items"]:
        run_self_build_approval_setter([], [])
        result = run_self_build_batch_cycle()
    else:
        first_id = queue["items"][0]["approval_id"]
        run_self_build_approval_setter([first_id], [])
        result = run_self_build_batch_cycle()
    assert result["status"] in {"COMPLETE", "STOPPED_APPLY", "STOPPED_POSTFLIGHT", "STOPPED_PREFLIGHT_NOT_GREEN", "WAITING_FOR_APPROVAL"}


def test_batch_outputs_phase_results_and_authority() -> None:
    run_self_build_approval_setter([], [])
    result = run_self_build_batch_cycle()
    assert "phase_results" in result
    assert result["authority"]["mutation"] is False
    assert result["authority"]["execution"] is False


def test_batch_feedback_summary_exists() -> None:
    run_self_build_approval_setter([], [])
    result = run_self_build_batch_cycle()
    assert "score_feedback" in result
    assert {"status", "ranked_count", "flagged_count", "blocked_count", "canonical_hash"}.issubset(result["score_feedback"].keys())


def test_batch_no_approval_status_unchanged() -> None:
    run_self_build_approval_setter([], [])
    result = run_self_build_batch_cycle()
    assert result["status"] in {"WAITING_FOR_APPROVAL", "STOPPED_PREFLIGHT_NOT_GREEN"}
