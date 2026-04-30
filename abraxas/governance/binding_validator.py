"""PATCH-004 expected subsystem binding validator."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import yaml

DRIFT_FLAGS = [
    "DUPLICATE_SUBSYSTEM_RISK",
    "STALE_SCHEMA",
    "AUTHORITY_DRIFT",
    "MISSING_TEST_COVERAGE",
]


def validate_bindings(repo_root: str | Path) -> Dict[str, object]:
    root = Path(repo_root).resolve()
    spec_path = root / ".aal" / "expected_subsystems.v1.yaml"
    if not spec_path.exists():
        return {
            "schema_version": "BindingValidationReport.v1",
            "status": "NOT_COMPUTABLE",
            "expected_subsystems_path": ".aal/expected_subsystems.v1.yaml",
            "subsystems": [],
            "missing_subsystems": [],
            "drift_flags": ["AUTHORITY_DRIFT"],
        }

    with spec_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}

    subsystems = payload.get("subsystems", [])
    seen_ids = set()
    records: List[Dict[str, object]] = []
    missing_subsystems: List[str] = []
    drift_flags = set()

    if payload.get("schema_version") != "ExpectedSubsystems.v1":
        drift_flags.add("STALE_SCHEMA")

    for subsystem in subsystems:
        subsystem_id = subsystem.get("id", "NOT_COMPUTABLE")
        required_paths = subsystem.get("required_paths") or []
        if subsystem_id in seen_ids:
            drift_flags.add("DUPLICATE_SUBSYSTEM_RISK")
        seen_ids.add(subsystem_id)

        states = []
        missing_paths = []
        for required in required_paths:
            target = root / required
            if not target.exists():
                states.append("MISSING_PATH")
                missing_paths.append(required)
            elif target.is_dir() and not any(target.rglob("*")):
                states.append("PARTIAL")
            else:
                states.append("PRESENT")

        status = "PRESENT"
        if not required_paths:
            status = "NOT_COMPUTABLE"
        elif "MISSING_PATH" in states:
            status = "MISSING_PATH"
            missing_subsystems.append(subsystem_id)
            drift_flags.add("AUTHORITY_DRIFT")
        elif "PARTIAL" in states:
            status = "PARTIAL"

        records.append(
            {
                "id": subsystem_id,
                "status": status,
                "required_paths": required_paths,
                "missing_paths": missing_paths,
            }
        )

    test_file = root / "tests" / "test_patch004_meta_governance.py"
    if not test_file.exists():
        drift_flags.add("MISSING_TEST_COVERAGE")

    overall_status = "PASS"
    if any(item["status"] in {"MISSING_PATH", "NOT_COMPUTABLE"} for item in records):
        overall_status = "FAIL"
    elif any(item["status"] == "PARTIAL" for item in records) or drift_flags:
        overall_status = "PARTIAL"

    return {
        "schema_version": "BindingValidationReport.v1",
        "status": overall_status,
        "expected_subsystems_path": ".aal/expected_subsystems.v1.yaml",
        "subsystems": records,
        "missing_subsystems": sorted(missing_subsystems),
        "drift_flags": sorted(set(drift_flags).intersection(DRIFT_FLAGS)),
    }
