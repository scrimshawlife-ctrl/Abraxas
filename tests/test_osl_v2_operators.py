from copy import deepcopy

from webpanel.core_bridge import core_ingest
from webpanel.models import AbraxasSignalPacket, RunState
from webpanel.osl_v2 import stable_hash
from webpanel.runplan import RunPlanStep, execute_step
from webpanel.structure_extract import MAX_METRICS, MAX_NODES, MAX_REFS, MAX_UNKNOWNS


def _ingest_run(packet: AbraxasSignalPacket) -> RunState:
    result = core_ingest(packet.model_dump())
    return RunState(**result)


def _packet(payload: dict, *, tier: str = "psychonaut", lane: str = "canon") -> AbraxasSignalPacket:
    return AbraxasSignalPacket(
        signal_id="sig-ops",
        timestamp_utc="2026-02-03T00:00:00+00:00",
        tier=tier,
        lane=lane,
        payload=payload,
        confidence={"score": "0.5"},
        provenance_status="partial",
        invariance_status="fail",
        drift_flags=["drift_a"],
        rent_status="paid",
        not_computable_regions=[],
    )


def _execute_step(run, kind: str) -> dict:
    step = RunPlanStep(
        step_id=f"01_{kind}",
        kind=kind,
        input_refs={},
        params={},
        produces="note",
        requires_human_confirmation=False,
    )
    result = execute_step(run, step)
    run.last_step_result = result
    run.step_results.append(result)
    return result


def test_extract_structure_bounded_no_mutation():
    payload = {"items": [{"value": idx} for idx in range(MAX_NODES + 10)]}
    packet = _packet(payload)
    run = _ingest_run(packet)
    original_payload = deepcopy(packet.payload)

    result = _execute_step(run, "extract_structure_v0")
    assert result is not None
    assert result["kind"] == "extract_structure_v0"
    assert len(result["paths"]) <= MAX_NODES
    assert len(result["numeric_metrics"]) <= MAX_METRICS
    assert len(result["evidence_refs"]) <= MAX_REFS
    assert len(result["unknowns"]) <= MAX_UNKNOWNS
    assert run.signal.payload == original_payload


def test_extract_structure_deterministic_hash():
    payload = {"alpha": {"beta": 1, "url": "https://example.com"}}
    run_a = _ingest_run(_packet(payload))
    run_b = _ingest_run(_packet(payload))

    result_a = _execute_step(run_a, "extract_structure_v0")
    result_b = _execute_step(run_b, "extract_structure_v0")
    assert stable_hash(result_a) == stable_hash(result_b)


def test_compress_signal_bounded_score():
    payload = {"alpha": {"beta": 3, "url": "https://example.com"}, "empty": {}, "none": None}
    run = _ingest_run(_packet(payload))
    _execute_step(run, "extract_structure_v0")
    result = _execute_step(run, "compress_signal_v0")
    assert result is not None
    assert result["kind"] == "compress_signal_v0"
    score = result["plan_pressure"]["score"]
    assert 0.0 <= score <= 1.0
    assert len(result.get("salient_metrics", [])) <= 10
    assert len(result.get("next_questions", [])) <= 6
    assert all(len(q) <= 120 for q in result.get("next_questions", []))


def test_compress_signal_missing_extract_returns_error():
    run = _ingest_run(_packet({"alpha": 1}))
    result = _execute_step(run, "compress_signal_v0")
    assert result["kind"] == "compress_signal_v0"
    assert result.get("error") == "missing_extract_structure_v0"


def _assert_no_exec_fields(actions: list[dict]) -> None:
    forbidden = {"exec", "cmd", "endpoint", "shell"}

    def walk(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                assert key not in forbidden
                walk(value)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(actions)


def test_propose_actions_deterministic_and_advisory_only():
    payload = {"alpha": {"beta": 1, "url": "https://example.com"}, "none": None}
    run_a = _ingest_run(_packet(payload))
    run_b = _ingest_run(_packet(payload))

    _execute_step(run_a, "extract_structure_v0")
    _execute_step(run_a, "compress_signal_v0")
    result_a = _execute_step(run_a, "propose_actions_v0")

    _execute_step(run_b, "extract_structure_v0")
    _execute_step(run_b, "compress_signal_v0")
    result_b = _execute_step(run_b, "propose_actions_v0")
    assert result_a["kind"] == "propose_actions_v0"
    assert result_b["kind"] == "propose_actions_v0"
    assert stable_hash(result_a) == stable_hash(result_b)
    assert len(result_a.get("actions", [])) <= 3
    _assert_no_exec_fields(result_a.get("actions", []))


def test_enterprise_tier_suppresses_actions():
    payload = {"alpha": {"beta": 9, "url": "https://example.com"}, "none": None}
    run = _ingest_run(_packet(payload, tier="enterprise", lane="canon"))
    _execute_step(run, "extract_structure_v0")
    _execute_step(run, "compress_signal_v0")
    result = _execute_step(run, "propose_actions_v0")
    assert result is not None
    assert result["kind"] == "propose_actions_v0"
    assert result.get("actions") == []
