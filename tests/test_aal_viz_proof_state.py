from abx.viz.proof_builder import build_proof_states


def _base_artifacts() -> tuple[dict, dict, dict]:
    report = {"schema_version": "CalibrationDriftReport.v1", "sha256": "sha256:r"}
    advisory = {"schema_version": "DomainWeightAdvisory.v1", "sha256": "sha256:a"}
    fusion = {"schema_version": "CrossDomainFusionProjection.v1", "sha256": "sha256:f"}
    return report, advisory, fusion


def _queue(priority_by_source: dict[str, str]) -> dict:
    items = []
    for source, priority in priority_by_source.items():
        items.append({"source_system": source, "priority": priority, "review_id": f"{source}.{priority.lower()}"})
    return {"items": items}


def test_missing_hash_display_blocked(monkeypatch):
    report, advisory, fusion = _base_artifacts()
    monkeypatch.setattr("abx.viz.proof_builder.resolve_source_hash", lambda *_args, **_kwargs: "NOT_COMPUTABLE")
    states = build_proof_states(report, advisory, fusion, _queue({}))
    assert all(state["display_allowed"] is False for state in states)
    assert all(state["display_status"] == "NOT_COMPUTABLE" for state in states)


def test_p0_review_blocks_visibility(monkeypatch):
    report, advisory, fusion = _base_artifacts()
    monkeypatch.setattr("abx.viz.proof_builder.resolve_source_hash", lambda *_args, **_kwargs: "sha256:ok")
    states = build_proof_states(report, advisory, fusion, _queue({"calibration": "P0"}))
    by_id = {s["projection_id"]: s for s in states}
    assert by_id["calibration_drift_report"]["display_allowed"] is False
    assert by_id["calibration_drift_report"]["display_status"] == "BLOCKED"


def test_p1_review_keeps_visibility_and_review_link(monkeypatch):
    report, advisory, fusion = _base_artifacts()
    monkeypatch.setattr("abx.viz.proof_builder.resolve_source_hash", lambda *_args, **_kwargs: "sha256:ok")
    states = build_proof_states(report, advisory, fusion, _queue({"fusion": "P1"}))
    by_id = {s["projection_id"]: s for s in states}
    fusion_state = by_id["fusion_projection"]
    assert fusion_state["display_allowed"] is True
    assert fusion_state["display_status"] == "OK"
    assert fusion_state["operator_review_item_id"] == "fusion.p1"


def test_no_review_visible_when_hash_present(monkeypatch):
    report, advisory, fusion = _base_artifacts()
    monkeypatch.setattr("abx.viz.proof_builder.resolve_source_hash", lambda *_args, **_kwargs: "sha256:ok")
    states = build_proof_states(report, advisory, fusion, _queue({}))
    assert all(state["display_allowed"] is True for state in states)
    assert all(state["display_status"] == "OK" for state in states)


def test_authority_lane_mapping_and_shadow_never_forecast(monkeypatch):
    report, advisory, fusion = _base_artifacts()
    monkeypatch.setattr("abx.viz.proof_builder.resolve_source_hash", lambda *_args, **_kwargs: "sha256:ok")
    states = build_proof_states(report, advisory, fusion, _queue({}))
    lane_by_id = {s["projection_id"]: s["authority_lane"] for s in states}
    assert lane_by_id["calibration_drift_report"] == "FORECAST"
    assert lane_by_id["domain_weight_advisory"] == "FORECAST"
    assert lane_by_id["fusion_projection"] == "PROJECTION"
    assert all(not (s["projection_id"] == "fusion_projection" and s["authority_lane"] == "FORECAST") for s in states)
