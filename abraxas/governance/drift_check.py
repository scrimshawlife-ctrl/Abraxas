"""
Canon State & Drift Guard v0.1.

Deterministic, read-only governance check for canon state drift.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml
except ImportError as exc:
    raise ImportError(
        "PyYAML required for canon state drift check. Install via: pip install pyyaml"
    ) from exc

DEFAULT_CANON_STATE_PATH = Path(".abraxas") / "canon_state.v0.yaml"

VALID_LANES = {"canon-active", "canon-shadow", "canary", "deprecated"}
VALID_IMPLEMENTATION_STATES = {
    "implemented",
    "engineering-queued",
    "design-locked",
    "drifted",
}

SEVERITY_ORDER = {"ERROR": 0, "WARN": 1, "INFO": 2}


@dataclass(frozen=True)
class DriftIssue:
    severity: str
    code: str
    message: str
    subsystem: str = "global"


@dataclass(frozen=True)
class DriftReport:
    system_name: str
    repo_version: str
    canon_state_version: str
    subsystems_declared: int
    issues: List[DriftIssue]

    def summary_counts(self) -> Dict[str, int]:
        counts = {"ERROR": 0, "WARN": 0, "INFO": 0}
        for issue in self.issues:
            if issue.severity in counts:
                counts[issue.severity] += 1
        counts["total"] = sum(counts.values())
        return counts

    def has_errors(self) -> bool:
        return any(issue.severity == "ERROR" for issue in self.issues)


def run_drift_check(
    repo_root: Optional[Path] = None,
    canon_path: Optional[Path] = None,
) -> Tuple[int, str]:
    repo_root = Path(repo_root) if repo_root else _default_repo_root()
    canon_path = Path(canon_path) if canon_path else repo_root / DEFAULT_CANON_STATE_PATH

    issues: List[DriftIssue] = []
    system_name = "unknown"
    repo_version = "unknown"
    canon_state_version = "unknown"
    subsystems_declared = 0

    if not canon_path.exists():
        issues.append(
            DriftIssue(
                severity="ERROR",
                code="canon_state_missing",
                message=f"Canon state file not found: {canon_path}",
            )
        )
        report = DriftReport(
            system_name=system_name,
            repo_version=repo_version,
            canon_state_version=canon_state_version,
            subsystems_declared=subsystems_declared,
            issues=issues,
        )
        return 2, format_report(report)

    try:
        state = _load_canon_state(canon_path)
    except Exception as exc:
        issues.append(
            DriftIssue(
                severity="ERROR",
                code="canon_state_unreadable",
                message=f"Failed to read canon state: {exc}",
            )
        )
        report = DriftReport(
            system_name=system_name,
            repo_version=repo_version,
            canon_state_version=canon_state_version,
            subsystems_declared=subsystems_declared,
            issues=issues,
        )
        return 2, format_report(report)

    if not isinstance(state, dict):
        issues.append(
            DriftIssue(
                severity="ERROR",
                code="invalid_canon_state_root",
                message="Canon state must be a mapping at the root level",
            )
        )
        report = DriftReport(
            system_name=system_name,
            repo_version=repo_version,
            canon_state_version=canon_state_version,
            subsystems_declared=subsystems_declared,
            issues=issues,
        )
        return 1, format_report(report)

    system_name = _require_string_field(
        state, "system_name", issues, field_scope="global"
    )
    repo_version = _require_string_field(
        state, "repo_version", issues, field_scope="global"
    )
    canon_state_version = _require_string_field(
        state, "canon_state_version", issues, field_scope="global"
    )

    governance_flags = state.get("governance_flags")
    if not isinstance(governance_flags, (dict, list)):
        issues.append(
            DriftIssue(
                severity="ERROR",
                code="invalid_governance_flags",
                message="governance_flags must be a mapping or list",
            )
        )

    subsystems = state.get("subsystems")
    if subsystems is None:
        issues.append(
            DriftIssue(
                severity="ERROR",
                code="missing_subsystems",
                message="subsystems list is required",
            )
        )
        subsystems = []
    if not isinstance(subsystems, list):
        issues.append(
            DriftIssue(
                severity="ERROR",
                code="invalid_subsystems_type",
                message="subsystems must be a list",
            )
        )
        subsystems = []

    subsystems_declared = len(subsystems)
    issues.extend(_validate_subsystems(subsystems, repo_root))

    report = DriftReport(
        system_name=system_name,
        repo_version=repo_version,
        canon_state_version=canon_state_version,
        subsystems_declared=subsystems_declared,
        issues=issues,
    )
    exit_code = 1 if report.has_errors() else 0
    return exit_code, format_report(report)


def format_report(report: DriftReport) -> str:
    counts = report.summary_counts()
    status = "CLEAN" if counts["total"] == 0 else "ISSUES"

    lines = [
        "CANON STATE DRIFT CHECK v0.1",
        f"system: {report.system_name}",
        f"repo_version: {report.repo_version}",
        f"canon_state_version: {report.canon_state_version}",
        f"subsystems_declared: {report.subsystems_declared}",
        (
            "issues_total: {total} (error={ERROR}, warn={WARN}, info={INFO})".format(
                **counts
            )
        ),
        f"status: {status}",
        "",
        "issues:",
    ]

    sorted_issues = _sorted_issues(report.issues)
    if not sorted_issues:
        lines.append("  - none")
    else:
        for issue in sorted_issues:
            lines.append(
                "  - {severity} | code={code} | subsystem={subsystem} | {message}".format(
                    severity=issue.severity,
                    code=issue.code,
                    subsystem=issue.subsystem,
                    message=issue.message,
                )
            )

    return "\n".join(lines)


def _sorted_issues(issues: List[DriftIssue]) -> List[DriftIssue]:
    return sorted(
        issues,
        key=lambda issue: (
            SEVERITY_ORDER.get(issue.severity, 99),
            issue.code,
            issue.subsystem,
            issue.message,
        ),
    )


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_canon_state(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data or {}


def _require_string_field(
    state: Dict[str, Any],
    field_name: str,
    issues: List[DriftIssue],
    field_scope: str,
) -> str:
    value = state.get(field_name)
    if not isinstance(value, str) or not value.strip():
        issues.append(
            DriftIssue(
                severity="ERROR",
                code="missing_field",
                message=f"Missing or invalid field: {field_name}",
                subsystem=field_scope,
            )
        )
        return "unknown"
    return value


def _validate_subsystems(
    subsystems: List[Any], repo_root: Path
) -> List[DriftIssue]:
    issues: List[DriftIssue] = []
    keys: List[str] = []

    for index, subsystem in enumerate(subsystems):
        if not isinstance(subsystem, dict):
            issues.append(
                DriftIssue(
                    severity="ERROR",
                    code="invalid_subsystem_entry",
                    message="Subsystem entry must be a mapping",
                    subsystem=f"index:{index}",
                )
            )
            continue

        subsystem_key = subsystem.get("key")
        subsystem_id = (
            subsystem_key if isinstance(subsystem_key, str) else f"index:{index}"
        )

        if not isinstance(subsystem_key, str) or not subsystem_key.strip():
            issues.append(
                DriftIssue(
                    severity="ERROR",
                    code="missing_field",
                    message="Subsystem key is required",
                    subsystem=subsystem_id,
                )
            )
        else:
            keys.append(subsystem_key)

        lane = subsystem.get("lane")
        if lane not in VALID_LANES:
            issues.append(
                DriftIssue(
                    severity="ERROR",
                    code="invalid_lane",
                    message=f"Invalid lane '{lane}'. Must be one of: {sorted(VALID_LANES)}",
                    subsystem=subsystem_id,
                )
            )

        impl_state = subsystem.get("implementation_state")
        if impl_state not in VALID_IMPLEMENTATION_STATES:
            issues.append(
                DriftIssue(
                    severity="ERROR",
                    code="invalid_implementation_state",
                    message=(
                        "Invalid implementation_state '{state}'. Must be one of: {valid}".format(
                            state=impl_state, valid=sorted(VALID_IMPLEMENTATION_STATES)
                        )
                    ),
                    subsystem=subsystem_id,
                )
            )

        path_value = subsystem.get("path")
        if not isinstance(path_value, str) or not path_value.strip():
            issues.append(
                DriftIssue(
                    severity="ERROR",
                    code="missing_field",
                    message="Subsystem path is required",
                    subsystem=subsystem_id,
                )
            )
        else:
            path_obj = Path(path_value)
            if not path_obj.is_absolute():
                path_obj = repo_root / path_obj
            if not path_obj.exists():
                issues.append(
                    DriftIssue(
                        severity="ERROR",
                        code="missing_path",
                        message=f"Subsystem path does not exist: {path_value}",
                        subsystem=subsystem_id,
                    )
                )

        registries = subsystem.get("registries")
        if registries is not None and not isinstance(registries, list):
            issues.append(
                DriftIssue(
                    severity="ERROR",
                    code="invalid_registries_type",
                    message="registries must be a list when provided",
                    subsystem=subsystem_id,
                )
            )
        elif isinstance(registries, list):
            for registry in registries:
                if not isinstance(registry, str) or not registry.strip():
                    issues.append(
                        DriftIssue(
                            severity="ERROR",
                            code="invalid_registry_path",
                            message="Registry path must be a non-empty string",
                            subsystem=subsystem_id,
                        )
                    )
                    continue
                registry_path = Path(registry)
                if not registry_path.is_absolute():
                    registry_path = repo_root / registry_path
                if not registry_path.exists():
                    issues.append(
                        DriftIssue(
                            severity="ERROR",
                            code="missing_registry",
                            message=f"Registry path does not exist: {registry}",
                            subsystem=subsystem_id,
                        )
                    )

    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    for dup in duplicates:
        issues.append(
            DriftIssue(
                severity="ERROR",
                code="duplicate_subsystem_key",
                message=f"Duplicate subsystem key detected: {dup}",
                subsystem=dup,
            )
        )

    return issues


def main() -> None:
    exit_code, output = run_drift_check()
    print(output)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
