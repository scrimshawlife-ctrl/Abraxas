from webpanel.osl_v2 import build_oracle_output_v2


def _provenance(drift_class: str = "none", passed: bool = True) -> dict:
    return {
        "input_hash": "hash_in",
        "policy_hash": "hash_policy",
        "operator_versions": {"extract_structure_v0": "v0"},
        "stability_status": {"passed": passed, "drift_class": drift_class},
    }


def test_suppressed_when_missing_inputs():
    output = build_oracle_output_v2(
        signal_id="sig-1",
        tier="psychonaut",
        lane="canon",
        indicators={"pressure": {"score": 0.5}},
        evidence=[],
        provenance=_provenance(),
        missing_inputs=["payload"],
        drift_class="none",
    )
    assert output["flags"]["suppressed"] is True
    assert output["flags"]["not_computable"]["reason"] == "missing_inputs"
    assert "payload" in output["flags"]["not_computable"]["missing_inputs"]


def test_suppressed_when_drift_detected():
    output = build_oracle_output_v2(
        signal_id="sig-2",
        tier="psychonaut",
        lane="canon",
        indicators={"pressure": {"score": 0.5}},
        evidence=[],
        provenance=_provenance(drift_class="input_variation", passed=False),
        missing_inputs=None,
        drift_class="input_variation",
    )
    assert output["flags"]["suppressed"] is True
    assert output["flags"]["not_computable"]["reason"] == "drift_class=input_variation"


def test_not_suppressed_when_inputs_present_and_stable():
    output = build_oracle_output_v2(
        signal_id="sig-3",
        tier="psychonaut",
        lane="canon",
        indicators={"pressure": {"score": 0.5}},
        evidence=[],
        provenance=_provenance(),
        missing_inputs=None,
        drift_class="none",
    )
    assert output["flags"]["suppressed"] is False
    assert "not_computable" not in output["flags"]
