from __future__ import annotations

import json
from pathlib import Path

import jsonschema


def _load_schema(name: str) -> dict:
    return json.loads((Path("schemas") / name).read_text(encoding="utf-8"))


def test_code_review_input_contract_accepts_minimal_payload() -> None:
    schema = _load_schema("CodeReviewInput.v1.json")
    payload = {
        "code_input": {
            "language": "python",
            "content": "print('ok')",
        },
        "context": {
            "rule_set_version": "code_review_contract.v1",
        },
        "include_patch_plan": False,
    }
    jsonschema.Draft202012Validator(schema).validate(payload)


def test_code_review_output_contract_accepts_shape_only_packet() -> None:
    schema = _load_schema("CodeReviewOutput.v1.json")
    payload = {
        "status": "OK",
        "issues": [
            {
                "issue_id": "ISSUE-1",
                "severity": "LOW",
                "category": "style",
                "message": "Example issue",
                "actionable_fix": "Apply formatter",
            }
        ],
        "summary": {
            "issue_count": 1,
            "max_severity": "LOW",
        },
        "patch_plan": ["Run formatter"],
        "provenance": {
            "contract": "RUNE.CODE.REVIEW.contract.v1",
            "evaluation_mode": "shape_only",
        },
    }
    jsonschema.Draft202012Validator(schema).validate(payload)


def test_code_review_output_contract_rejects_unknown_severity() -> None:
    schema = _load_schema("CodeReviewOutput.v1.json")
    payload = {
        "status": "OK",
        "issues": [
            {
                "issue_id": "ISSUE-2",
                "severity": "SEVERE",
                "category": "logic",
                "message": "Invalid severity",
                "actionable_fix": "Use allowed severity enum",
            }
        ],
        "summary": {
            "issue_count": 1,
            "max_severity": "HIGH",
        },
        "patch_plan": None,
        "provenance": {
            "contract": "RUNE.CODE.REVIEW.contract.v1",
            "evaluation_mode": "shape_only",
        },
    }

    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda e: e.path)
    assert errors
    assert "SEVERE" in errors[0].message
