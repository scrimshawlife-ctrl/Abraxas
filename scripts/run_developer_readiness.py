from __future__ import annotations

import json
import hashlib
import os
import platform
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "out" / "reports" / "developer_readiness.json"


@dataclass(frozen=True)
class CheckSpec:
    check_id: str
    label: str
    command: List[str]
    required_files: List[Path]


CHECKS: List[CheckSpec] = [
    CheckSpec(
        check_id="optional_dependency_boundary_check",
        label="Optional dependency boundary check",
        command=["python", "scripts/check_optional_dependency_boundaries.py"],
        required_files=[ROOT / "scripts" / "check_optional_dependency_boundaries.py"],
    ),
    CheckSpec(
        check_id="find_skills_tests",
        label="Find Skills tests",
        command=["pytest", "-q", "tests/test_find_skills.py"],
        required_files=[ROOT / "tests" / "test_find_skills.py"],
    ),
    CheckSpec(
        check_id="code_review_contract_tests",
        label="Code Review contract tests",
        command=["pytest", "-q", "tests/test_code_review_contract.py"],
        required_files=[ROOT / "tests" / "test_code_review_contract.py"],
    ),
    CheckSpec(
        check_id="optional_dependency_tests",
        label="Optional dependency tests",
        command=["pytest", "-q", "tests/test_optional_dependencies.py", "tests/test_check_optional_dependency_boundaries.py"],
        required_files=[ROOT / "tests" / "test_optional_dependencies.py", ROOT / "tests" / "test_check_optional_dependency_boundaries.py"],
    ),
    CheckSpec(
        check_id="webpanel_operator_tests",
        label="Webpanel/operator tests",
        command=["pytest", "-q", "tests/test_webpanel_execution_validation.py", "tests/test_webpanel_oracle_compare.py", "tests/test_webpanel_run_filters.py", "tests/test_operator.py", "tests/test_operator_run_console.py", "tests/test_operator_surface_route_wiring.py"],
        required_files=[ROOT / "tests"],
    ),
    CheckSpec(
        check_id="execution_sanity_pack",
        label="Execution validator/oracle compare/run filter sanity pack",
        command=[
            "pytest",
            "-q",
            "tests/test_execution_validator.py",
            "tests/test_webpanel_execution_validation.py",
            "tests/test_run_diff_summary.py",
            "tests/test_webpanel_oracle_compare.py",
            "tests/test_webpanel_run_filters.py",
        ],
        required_files=[
            ROOT / "tests" / "test_execution_validator.py",
            ROOT / "tests" / "test_webpanel_execution_validation.py",
            ROOT / "tests" / "test_run_diff_summary.py",
            ROOT / "tests" / "test_webpanel_oracle_compare.py",
            ROOT / "tests" / "test_webpanel_run_filters.py",
        ],
    ),
    CheckSpec(
        check_id="architecture_svg_bounds_check",
        label="Architecture SVG bounds check",
        command=["python", "scripts/check_architecture_svg_bounds.py"],
        required_files=[ROOT / "scripts" / "check_architecture_svg_bounds.py", ROOT / "docs" / "assets" / "architecture" / "abraxas-architecture-overview.svg"],
    ),
]


def _shell_join(parts: List[str]) -> str:
    return " ".join(parts)


def _run_check(spec: CheckSpec) -> dict:
    missing = [str(path.relative_to(ROOT)) for path in spec.required_files if not path.exists()]
    if missing:
        return {
            "check_id": spec.check_id,
            "label": spec.label,
            "command": _shell_join(spec.command),
            "status": "NOT_PRESENT",
            "return_code": None,
            "stdout": "",
            "stderr": "",
            "missing_files": missing,
        }

    try:
        completed = subprocess.run(
            spec.command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as exc:
        return {
            "check_id": spec.check_id,
            "label": spec.label,
            "command": _shell_join(spec.command),
            "status": "NOT_COMPUTABLE",
            "return_code": None,
            "stdout": "",
            "stderr": str(exc),
            "missing_files": [],
        }
    return {
        "check_id": spec.check_id,
        "label": spec.label,
        "command": _shell_join(spec.command),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "return_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "missing_files": [],
    }


def _derive_overall_status(checks: List[dict]) -> str:
    statuses = [row["status"] for row in checks]
    if any(status == "NOT_COMPUTABLE" for status in statuses):
        return "NOT_COMPUTABLE"
    if any(status == "FAIL" for status in statuses):
        return "FAIL"
    if any(status == "NOT_PRESENT" for status in statuses):
        return "PARTIAL"
    if all(status == "PASS" for status in statuses):
        return "PASS"
    return "NOT_COMPUTABLE"


def main() -> int:
    run_id = f"DEV-READINESS-{uuid4().hex[:12].upper()}"
    timestamp = datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")

    checks = [_run_check(spec) for spec in CHECKS]
    missing_surfaces = [
        {"check_id": row["check_id"], "missing_files": row.get("missing_files", [])}
        for row in checks
        if row["status"] == "NOT_PRESENT"
    ]

    recommended_next_actions = []
    for row in checks:
        if row["status"] == "FAIL":
            recommended_next_actions.append(f"Investigate failed check: {row['check_id']}")
        if row["status"] == "NOT_PRESENT":
            recommended_next_actions.append(f"Add missing surface(s) for check: {row['check_id']}")

    report = {
        "run_id": run_id,
        "timestamp_utc": timestamp,
        "status": _derive_overall_status(checks),
        "checks": checks,
        "missing_surfaces": missing_surfaces,
        "recommended_next_actions": recommended_next_actions,
        "provenance": {
            "script": "scripts/run_developer_readiness.py",
            "schema_version": "developer_readiness_report.v1",
            "deterministic_ordering": [spec.check_id for spec in CHECKS],
            "input_hash": hashlib.sha256(
                "|".join(
                    f"{spec.check_id}:{_shell_join(spec.command)}:{','.join(str(path.relative_to(ROOT)) for path in spec.required_files)}"
                    for spec in CHECKS
                ).encode("utf-8")
            ).hexdigest(),
            "execution_environment": {
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "cwd": str(ROOT),
                "ci": "true" if os.getenv("CI") else "false",
            },
            "gap_closure_run_id_linkage": os.getenv("GAP_CLOSURE_RUN_ID", "NOT_COMPUTABLE"),
        },
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"developer-readiness report written: {REPORT_PATH.relative_to(ROOT)}")
    print(f"status={report['status']}")
    for row in checks:
        print(f"- {row['check_id']}: {row['status']}")

    return 0 if report["status"] in {"PASS", "PARTIAL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
