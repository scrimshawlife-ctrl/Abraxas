from __future__ import annotations

from abx.codex.validate.bell_validator import validate_bell_constraint


def test_bell_validator_triple_bucket_detection():
    payload = {
        "notes": [
            "Enforce strict module independence (no global coupling).",
            "Use a fixed meaning dictionary: symbols are context-independent.",
            "The hidden cause explains the correlation with causal certainty.",
        ]
    }
    finding = validate_bell_constraint("module", "TEST_MODULE", payload)
    assert finding is not None
    assert finding.subject_id == "TEST_MODULE"
    assert finding.buckets["locality"]
    assert finding.buckets["realism"]
    assert finding.buckets["hidden"]
    assert finding.provenance["content_sha256"] and len(finding.provenance["content_sha256"]) == 64


def test_bell_validator_no_false_positive_when_missing_bucket():
    payload = {
        "notes": [
            "Allow global coupling when needed.",
            "Context determines meaning; do not assume fixed semantics.",
        ]
    }
    finding = validate_bell_constraint("module", "SAFE_MODULE", payload)
    assert finding is None
