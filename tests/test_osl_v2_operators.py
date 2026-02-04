from copy import deepcopy

from webpanel import app as webpanel_app
from webpanel.core_bridge import _STEP_STATE
from webpanel.ledger import LedgerChain
from webpanel.models import AbraxasSignalPacket, DeferralStart
from webpanel.osl_v2 import stable_hash
from webpanel.runplan import RunPlanStep, execute_step
from webpanel.store import InMemoryStore
from webpanel.structure_extract import MAX_METRICS, MAX_NODES, MAX_REFS, MAX_UNKNOWNS


def _reset_webpanel() -> None:
    webpanel_app.store = InMemoryStore()
    webpanel_app.ledger = LedgerChain()
    _STEP_STATE.clear()


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


def _run_steps(run_id: str, steps: int) -> None:
    webpanel_app._start_deferral(run_id, DeferralStart(quota_max_actions=3))
    for _ in range(steps):
        webpanel_app._step_deferral(run_id)


def test_extract_structure_bounded_no_mutation():
    _reset_webpanel()
    payload = {"items": [{"value": idx} for idx in range(MAX_NODES + 10)]}
    packet = _packet(payload)
    resp = webpanel_app.ingest(packet)
    run_id = resp["run_id"]
    original_payload = deepcopy(packet.payload)

    webpanel_app._start_deferral(run_id, DeferralStart(quota_max_actions=2))
    webpanel_app._step_deferral(run_id)

    run = webpanel_app.store.get(run_id)
    assert run is not None
    result = run.last_step_result
    assert result is not None
    assert result["kind"] == "extract_structure_v0"
    assert len(result["paths"]) <= MAX_NODES
    assert len(result["numeric_metrics"]) <= MAX_METRICS
    assert len(result["evidence_refs"]) <= MAX_REFS
    assert len(result["unknowns"]) <= MAX_UNKNOWNS
    assert run.signal.payload == original_payload


def test_extract_structure_deterministic_hash():
    _reset_webpanel()
    payload = {"alpha": {"beta": 1, "url": "https://example.com"}}
    resp_a = webpanel_app.ingest(_packet(payload))
    resp_b = webpanel_app.ingest(_packet(payload))

    webpanel_app._start_deferral(resp_a["run_id"], DeferralStart(quota_max_actions=2))
    webpanel_app._step_deferral(resp_a["run_id"])

    webpanel_app._start_deferral(resp_b["run_id"], DeferralStart(quota_max_actions=2))
    webpanel_app._step_deferral(resp_b["run_id"])

    run_a = webpanel_app.store.get(resp_a["run_id"])
    run_b = webpanel_app.store.get(resp_b["run_id"])
    assert run_a is not None and run_b is not None
    assert stable_hash(run_a.last_step_result) == stable_hash(run_b.last_step_result)


def test_compress_signal_bounded_score():
    _reset_webpanel()
    payload = {"alpha": {"beta": 3, "url": "https://example.com"}, "empty": {}, "none": None}
    resp = webpanel_app.ingest(_packet(payload))
    _run_steps(resp["run_id"], 2)

    run = webpanel_app.store.get(resp["run_id"])
    assert run is not None
    result = run.last_step_result
    assert result is not None
    assert result["kind"] == "compress_signal_v0"
    score = result["plan_pressure"]["score"]
    assert 0.0 <= score <= 1.0
    assert len(result.get("salient_metrics", [])) <= 10
    assert len(result.get("next_questions", [])) <= 6
    assert all(len(q) <= 120 for q in result.get("next_questions", []))


def test_compress_signal_missing_extract_returns_error():
    _reset_webpanel()
    resp = webpanel_app.ingest(_packet({"alpha": 1}))
    run = webpanel_app.store.get(resp["run_id"])
    assert run is not None

    step = RunPlanStep(
        step_id="01_compress_signal_v0",
        kind="compress_signal_v0",
        input_refs={},
        params={},
        produces="note",
        requires_human_confirmation=False,
    )
    result = execute_step(run, step)
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
    _reset_webpanel()
    payload = {"alpha": {"beta": 1, "url": "https://example.com"}, "none": None}
    resp_a = webpanel_app.ingest(_packet(payload))
    resp_b = webpanel_app.ingest(_packet(payload))

    _run_steps(resp_a["run_id"], 3)
    _run_steps(resp_b["run_id"], 3)

    run_a = webpanel_app.store.get(resp_a["run_id"])
    run_b = webpanel_app.store.get(resp_b["run_id"])
    assert run_a is not None and run_b is not None

    result_a = run_a.last_step_result
    result_b = run_b.last_step_result
    assert result_a["kind"] == "propose_actions_v0"
    assert result_b["kind"] == "propose_actions_v0"
    assert stable_hash(result_a) == stable_hash(result_b)
    assert len(result_a.get("actions", [])) <= 3
    _assert_no_exec_fields(result_a.get("actions", []))


def test_enterprise_tier_suppresses_actions():
    _reset_webpanel()
    payload = {"alpha": {"beta": 9, "url": "https://example.com"}, "none": None}
    resp = webpanel_app.ingest(_packet(payload, tier="enterprise", lane="canon"))
    _run_steps(resp["run_id"], 3)

    run = webpanel_app.store.get(resp["run_id"])
    assert run is not None
    result = run.last_step_result
    assert result is not None
    assert result["kind"] == "propose_actions_v0"
    assert result.get("actions") == []
