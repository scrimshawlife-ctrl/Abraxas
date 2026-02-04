from __future__ import annotations

from jinja2 import Environment, FileSystemLoader

from webpanel.core_bridge import core_ingest
from webpanel.models import AbraxasSignalPacket, RunState
from webpanel.oracle_output import build_oracle_json, build_oracle_view, validate_oracle_output_v2


def _packet() -> AbraxasSignalPacket:
    return AbraxasSignalPacket(
        signal_id="sig-oracle-render",
        timestamp_utc="2026-02-03T00:00:00+00:00",
        tier="psychonaut",
        lane="canon",
        payload={"alpha": {"beta": 1}},
        confidence={"score": "0.5"},
        provenance_status="complete",
        invariance_status="pass",
        drift_flags=[],
        rent_status="paid",
        not_computable_regions=[],
    )


def _oracle_output() -> dict:
    return {
        "signal_id": "sig-oracle-render",
        "tier": "psychonaut",
        "lane": "canon",
        "indicators": {"score": 0.9, "summary": "ok"},
        "evidence": ["ref-a", {"id": "ref-b"}],
        "flags": {"suppressed": False},
        "provenance": {
            "input_hash": "inputhash",
            "policy_hash": "policyhash",
            "operator_versions": {"extract_structure_v0": "v0"},
            "stability_status": {"passed": True, "drift_class": "none"},
        },
    }


def _run_state() -> RunState:
    result = core_ingest(_packet().model_dump())
    run = RunState(**result)
    run.oracle_output = _oracle_output()
    return run


def test_run_template_renders_oracle_section():
    run = _run_state()
    oracle_view = build_oracle_view(run.oracle_output)
    valid, errors = validate_oracle_output_v2(run.oracle_output)
    env = Environment(loader=FileSystemLoader("webpanel/templates"), autoescape=True)
    template = env.get_template("run.html")
    rendered = template.render(
        run=run,
        events=[],
        chain_valid=True,
        lineage_ids=[],
        panel_token="",
        panel_host="",
        panel_port="",
        token_enabled=False,
        current_policy_hash="",
        current_policy_snapshot={},
        policy_status="UNKNOWN",
        policy_diff_keys=[],
        oracle_view=oracle_view,
        oracle_validation={"valid": valid, "errors": errors},
    )
    assert "Oracle (OSLv2)" in rendered
    assert "Download oracle.json" in rendered
    assert "Indicators" in rendered
    assert "Evidence" in rendered


def test_oracle_json_payload_contains_keys():
    run = _run_state()
    payload = build_oracle_json(run)
    assert payload is not None
    assert '"signal_id"' in payload
    assert '"provenance"' in payload
