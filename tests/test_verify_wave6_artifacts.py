from __future__ import annotations

import scripts.verify_wave6_artifacts as verify_mod


def test_verify_passes_when_metrics_align() -> None:
    stub_index = {"summary": {"total_stubs": 4}}
    taxonomy = {"gap_summary": {"implementation_gap": 1, "policy_block": 0, "intentional_abstract": 3}}
    sync = {
        "metrics": {
            "total_stubs": 4,
            "implementation_gap": 1,
            "policy_block": 0,
            "intentional_abstract": 3,
        },
        "tasks": [
            {"id": "operator_gap_burn_down"},
            {"id": "policy_guardrails"},
            {"id": "intentional_abstract_inventory"},
        ],
        "status": {"evidence_backed": True},
    }

    ok, errors = verify_mod.verify(stub_index=stub_index, taxonomy=taxonomy, notion_sync=sync)

    assert ok is True
    assert errors == []


def test_verify_fails_on_metric_drift_and_missing_task() -> None:
    stub_index = {"summary": {"total_stubs": 4}}
    taxonomy = {"gap_summary": {"implementation_gap": 2, "policy_block": 1, "intentional_abstract": 1}}
    sync = {
        "metrics": {
            "total_stubs": 3,
            "implementation_gap": 1,
            "policy_block": 1,
            "intentional_abstract": 1,
        },
        "tasks": [{"id": "operator_gap_burn_down"}],
        "status": {"evidence_backed": False},
    }

    ok, errors = verify_mod.verify(stub_index=stub_index, taxonomy=taxonomy, notion_sync=sync)

    assert ok is False
    assert any("metrics.total_stubs mismatch" in err for err in errors)
    assert any("metrics.implementation_gap mismatch" in err for err in errors)
    assert any("missing tasks:" in err for err in errors)
    assert any("status.evidence_backed" in err for err in errors)
