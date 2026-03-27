from __future__ import annotations

from abx.boundary.adapterContainment import build_adapter_containment_report
from abx.boundary.inputEnvelope import build_input_envelope
from abx.boundary.interfaceClassification import detect_redundant_entrypoints
from abx.boundary.interfaceContracts import build_interface_contracts
from abx.boundary.interfaceOwnership import interface_ownership_report
from abx.boundary.normalization import normalize_envelope
from abx.boundary.scorecard import build_boundary_health_scorecard
from abx.boundary.trustEnforcement import enforce_trust_for_authoritative_mutation
from abx.boundary.trustReports import build_trust_report
from abx.boundary.validation import validate_envelope


def _valid_envelope():
    return build_input_envelope(
        source="external.feed",
        interface_id="runtime_orchestrator.execute_run_plan",
        payload={"run_id": " run-1 ", "scenario_id": " scn-1 "},
        received_tick=1,
    )


def test_envelope_validation_and_malformed_stale_partial_classification() -> None:
    env = _valid_envelope()
    assert validate_envelope(env, current_tick=1).status == "ACCEPTED"

    partial = build_input_envelope(source="external.feed", interface_id="runtime_orchestrator.execute_run_plan", payload={"run_id": "RUN"}, received_tick=1)
    assert validate_envelope(partial, current_tick=1).status == "DEGRADED"

    stale = _valid_envelope()
    assert validate_envelope(stale, current_tick=10).state == "STALE"


def test_normalization_and_provenance_carry_through_is_deterministic() -> None:
    env = _valid_envelope()
    a = normalize_envelope(env)
    b = normalize_envelope(env)
    assert a[0].__dict__ == b[0].__dict__
    assert a[1].trust_state == "EXTERNAL_ASSERTED"
    assert a[0].normalized_payload["run_id"] == "RUN-1"


def test_interface_contract_shape_and_ownership_stability() -> None:
    a = [x.__dict__ for x in build_interface_contracts()]
    b = [x.__dict__ for x in build_interface_contracts()]
    assert a == b
    owners = interface_ownership_report()
    assert "runtime" in owners
    assert isinstance(detect_redundant_entrypoints(), list)


def test_boundary_error_serialization_and_trust_enforcement() -> None:
    blocked = build_input_envelope(source="untrusted.raw", interface_id="runtime_orchestrator.execute_run_plan", payload={"run_id": "R", "scenario_id": "S"})
    decision = enforce_trust_for_authoritative_mutation(blocked)
    assert decision.status == "REJECTED"
    assert decision.errors[0].code == "BOUNDARY_REJECTED"


def test_adapter_containment_and_transform_metadata_stability() -> None:
    a = build_adapter_containment_report()
    b = build_adapter_containment_report()
    assert a == b
    assert a["status"] in {"PASS", "FAIL"}
    assert "transforms" in a


def test_boundary_scorecard_determinism_and_blockers() -> None:
    envelope = _valid_envelope()
    validation = validate_envelope(envelope, current_tick=1)
    normalized, provenance = normalize_envelope(envelope)
    validation_report = {
        "artifactType": "BoundaryValidationReport.v1",
        "normalizedCount": 1,
        "provenanceCount": 1,
        "reportHash": "validation-hash",
        "validation": validation.__dict__ | {"errors": [x.__dict__ for x in validation.errors]},
        "normalized": [normalized.__dict__],
        "provenance": [provenance.__dict__],
    }
    trust_report = build_trust_report([envelope])
    a = build_boundary_health_scorecard(validation_report, trust_report)
    b = build_boundary_health_scorecard(validation_report, trust_report)
    assert a.__dict__ == b.__dict__
    assert isinstance(a.blockers, list)


def test_invariance_reports_for_boundary_and_trust() -> None:
    env = _valid_envelope()
    v1 = validate_envelope(env, current_tick=1)
    v2 = validate_envelope(env, current_tick=1)
    assert v1.__dict__ == v2.__dict__

    t1 = build_trust_report([env])
    t2 = build_trust_report([env])
    assert t1 == t2
