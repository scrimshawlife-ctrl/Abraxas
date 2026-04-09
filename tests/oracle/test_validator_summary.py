from abraxas.oracle.proof.validator_summary import build_validator_summary_v2


def test_validator_summary_not_computable_listed() -> None:
    out = {
        "run_id": "r1",
        "lane": "shadow",
        "authority_advisory_boundary_enforced": True,
        "authority": {"signal_items": [1]},
        "advisory_attachments": [{"attachment_id": "trend", "status": "NOT_COMPUTABLE", "computable": False}],
    }
    summary = build_validator_summary_v2(output=out, hashes={"input_hash": "a", "authority_hash": "b", "full_hash": "c"}, artifact_refs=[])
    assert summary["not_computable_attachments"] == ["trend"]
