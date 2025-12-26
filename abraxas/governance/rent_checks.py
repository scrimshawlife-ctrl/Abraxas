"""
Rent Checks — The Enforcement Gate

Validates that manifests actually prove their rent claims.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class RentCheckReport:
    """Report from rent enforcement checks."""

    passed: bool
    failures: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    provenance: Dict[str, Any] = field(default_factory=dict)
    manifest_count: int = 0
    checks_run: int = 0

    def add_failure(self, manifest_id: str, check: str, message: str):
        """Add a failure to the report."""
        self.failures.append(
            {"manifest_id": manifest_id, "check": check, "message": message}
        )
        self.passed = False

    def add_warning(self, manifest_id: str, check: str, message: str):
        """Add a warning to the report."""
        self.warnings.append(
            {"manifest_id": manifest_id, "check": check, "message": message}
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "passed": self.passed,
            "failures": self.failures,
            "warnings": self.warnings,
            "provenance": self.provenance,
            "manifest_count": self.manifest_count,
            "checks_run": self.checks_run,
        }


def check_tests_exist(manifest: Dict[str, Any], repo_root: str) -> List[str]:
    """
    Check that all declared tests are discoverable.

    Args:
        manifest: Rent manifest dict
        repo_root: Repository root directory

    Returns:
        List of error messages (empty if all tests exist)
    """
    errors = []
    tests = manifest.get("proof", {}).get("tests", [])

    for test in tests:
        # Parse pytest node ID: path/to/test.py::test_function
        if "::" not in test:
            errors.append(f"Invalid test format (must be path::test_name): {test}")
            continue

        test_file = test.split("::")[0]
        test_path = Path(repo_root) / test_file

        if not test_path.exists():
            errors.append(f"Test file does not exist: {test_file}")

    return errors


def check_golden_files_declared(manifest: Dict[str, Any], repo_root: str) -> List[str]:
    """
    Check that golden files are declared.

    Note: Files don't need to exist yet (they may be created by tests),
    but they should be declared if tests produce golden outputs.

    Args:
        manifest: Rent manifest dict
        repo_root: Repository root directory

    Returns:
        List of warning messages (not errors)
    """
    warnings = []
    golden_files = manifest.get("proof", {}).get("golden_files", [])

    # If tests exist but no golden files declared, warn
    tests = manifest.get("proof", {}).get("tests", [])
    if len(tests) > 0 and len(golden_files) == 0:
        warnings.append("Tests declared but no golden files specified")

    return warnings


def check_ledgers_declared(manifest: Dict[str, Any]) -> List[str]:
    """
    Check that ledgers touched are declared.

    Note: Ledger paths don't need to exist yet (they may be created at runtime),
    but should follow conventions.

    Args:
        manifest: Rent manifest dict

    Returns:
        List of warning messages
    """
    warnings = []
    ledgers = manifest.get("proof", {}).get("ledgers_touched", [])

    if len(ledgers) == 0:
        warnings.append("No ledgers declared (component doesn't touch any ledgers)")

    # Check path conventions
    for ledger in ledgers:
        if not ledger.endswith(".jsonl"):
            warnings.append(
                f"Ledger path should end with .jsonl: {ledger}"
            )

    return warnings


def check_cost_model_present(manifest: Dict[str, Any]) -> List[str]:
    """
    Check that cost model is present and valid.

    Args:
        manifest: Rent manifest dict

    Returns:
        List of error messages
    """
    errors = []
    cost_model = manifest.get("cost_model", {})

    if not cost_model:
        errors.append("Missing cost_model section")
        return errors

    # Check required fields (validation should have already caught this)
    required = ["time_ms_expected", "memory_kb_expected", "io_expected"]
    for field in required:
        if field not in cost_model:
            errors.append(f"cost_model missing required field: {field}")

    return errors


def check_operator_edges_declared(
    manifest: Dict[str, Any], ter_spec: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Check that operator TER edges are declared and valid.

    Args:
        manifest: Rent manifest dict
        ter_spec: Optional TER specification (if available)

    Returns:
        List of error messages
    """
    errors = []

    if manifest.get("kind") != "operator":
        return errors  # Only applies to operators

    ter_edges = manifest.get("ter_edges_claimed", [])

    # If TER spec exists, validate edges are subset
    if ter_spec and ter_edges:
        valid_edges = ter_spec.get("edges", [])
        valid_edge_set = {
            (e["from"], e["to"]) for e in valid_edges if "from" in e and "to" in e
        }

        for edge in ter_edges:
            edge_tuple = (edge.get("from"), edge.get("to"))
            if edge_tuple not in valid_edge_set:
                errors.append(
                    f"TER edge not in spec: {edge['from']} -> {edge['to']}"
                )

    return errors


def check_expected_cost_bounds(
    manifest: Dict[str, Any], observed_stats: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Check that observed costs don't exceed expected costs by too much.

    Args:
        manifest: Rent manifest dict
        observed_stats: Optional observed performance stats from prior runs

    Returns:
        List of warning messages
    """
    warnings = []

    if not observed_stats:
        return warnings  # Skip if no observed data

    cost_model = manifest.get("cost_model", {})
    manifest_id = manifest.get("id", "unknown")

    # Check time
    expected_time = cost_model.get("time_ms_expected", 0)
    observed_time = observed_stats.get("time_ms_observed", 0)

    if observed_time > expected_time * 2:  # More than 2x expected
        warnings.append(
            f"Observed time ({observed_time}ms) exceeds expected ({expected_time}ms) by >2x"
        )

    # Check memory
    expected_memory = cost_model.get("memory_kb_expected", 0)
    observed_memory = observed_stats.get("memory_kb_observed", 0)

    if observed_memory > expected_memory * 2:
        warnings.append(
            f"Observed memory ({observed_memory}KB) exceeds expected ({expected_memory}KB) by >2x"
        )

    return warnings


def check_backtest_threshold(
    manifest: Dict[str, Any], backtest_ledger_path: Path
) -> List[str]:
    """
    Check that backtest pass rate meets threshold.

    This check validates predictive claims by requiring forecasts to pass
    backtest evaluation against historical data.

    Args:
        manifest: Rent manifest dict
        backtest_ledger_path: Path to backtest ledger

    Returns:
        List of error messages (empty if check passes)
    """
    errors = []

    # Check if backtest threshold declared
    thresholds = manifest.get("rent_claim", {}).get("thresholds", {})
    if "backtest_pass_rate_min" not in thresholds:
        return errors  # No backtest requirement

    min_pass_rate = thresholds["backtest_pass_rate_min"]

    # Check if backtest cases declared
    backtest_cases = manifest.get("proof", {}).get("backtest_cases", [])
    if not backtest_cases:
        errors.append("backtest_pass_rate_min declared but no backtest_cases in proof")
        return errors

    # Load backtest ledger
    if not backtest_ledger_path.exists():
        errors.append(f"Backtest ledger not found: {backtest_ledger_path}")
        return errors

    # Import here to avoid circular dependency
    try:
        from abraxas.backtest.ledger import BacktestLedger

        ledger = BacktestLedger(ledger_path=backtest_ledger_path)
        results = ledger.get_results_for_cases(backtest_cases, latest_only=True)
    except ImportError:
        errors.append("Backtest module not available")
        return errors
    except Exception as e:
        errors.append(f"Error loading backtest results: {e}")
        return errors

    if not results:
        errors.append(f"No backtest results found for cases: {backtest_cases}")
        return errors

    # Compute pass rate
    hits = sum(1 for r in results if r.get("status") == "HIT")
    total = len(results)

    pass_rate = hits / total

    if pass_rate < min_pass_rate:
        errors.append(
            f"Backtest pass rate {pass_rate:.2%} below threshold {min_pass_rate:.2%} "
            f"({hits}/{total} cases passed)"
        )

    return errors


def run_all_rent_checks(
    manifests: Dict[str, List[Dict[str, Any]]],
    repo_root: str,
    ter_spec: Optional[Dict[str, Any]] = None,
    observed_stats: Optional[Dict[str, Dict[str, Any]]] = None,
    backtest_ledger_path: Optional[Path] = None,
) -> RentCheckReport:
    """
    Run all rent checks on all manifests.

    Args:
        manifests: Dictionary of manifests by kind
        repo_root: Repository root directory
        ter_spec: Optional TER specification
        observed_stats: Optional observed performance stats by manifest ID
        backtest_ledger_path: Optional path to backtest ledger

    Returns:
        RentCheckReport with results
    """
    report = RentCheckReport(passed=True)
    report.provenance = {
        "timestamp": datetime.utcnow().isoformat(),
        "repo_root": repo_root,
        "ter_spec_provided": ter_spec is not None,
        "observed_stats_provided": observed_stats is not None,
    }

    all_manifests = []
    for kind in ["metrics", "operators", "artifacts"]:
        all_manifests.extend(manifests.get(kind, []))

    report.manifest_count = len(all_manifests)

    for manifest in all_manifests:
        manifest_id = manifest.get("id", "unknown")
        checks_for_manifest = 0

        # Check 1: Tests exist
        test_errors = check_tests_exist(manifest, repo_root)
        checks_for_manifest += 1
        for error in test_errors:
            report.add_failure(manifest_id, "tests_exist", error)

        # Check 2: Golden files declared
        golden_warnings = check_golden_files_declared(manifest, repo_root)
        checks_for_manifest += 1
        for warning in golden_warnings:
            report.add_warning(manifest_id, "golden_files_declared", warning)

        # Check 3: Ledgers declared
        ledger_warnings = check_ledgers_declared(manifest)
        checks_for_manifest += 1
        for warning in ledger_warnings:
            report.add_warning(manifest_id, "ledgers_declared", warning)

        # Check 4: Cost model present
        cost_errors = check_cost_model_present(manifest)
        checks_for_manifest += 1
        for error in cost_errors:
            report.add_failure(manifest_id, "cost_model_present", error)

        # Check 5: Operator edges (if applicable)
        if manifest.get("kind") == "operator":
            edge_errors = check_operator_edges_declared(manifest, ter_spec)
            checks_for_manifest += 1
            for error in edge_errors:
                report.add_failure(manifest_id, "operator_edges_declared", error)

        # Check 6: Cost bounds (if observed stats available)
        if observed_stats and manifest_id in observed_stats:
            cost_warnings = check_expected_cost_bounds(
                manifest, observed_stats[manifest_id]
            )
            checks_for_manifest += 1
            for warning in cost_warnings:
                report.add_warning(manifest_id, "expected_cost_bounds", warning)

        # Check 7: Backtest threshold (if declared and ledger available)
        if backtest_ledger_path:
            backtest_errors = check_backtest_threshold(manifest, backtest_ledger_path)
            if backtest_errors:  # Only count check if threshold was declared
                checks_for_manifest += 1
                for error in backtest_errors:
                    report.add_failure(manifest_id, "backtest_threshold", error)

        report.checks_run += checks_for_manifest

    return report


def format_report_console(report: RentCheckReport) -> str:
    """Format report for console output."""
    lines = []
    lines.append("=" * 60)
    lines.append("RENT ENFORCEMENT REPORT")
    lines.append("=" * 60)
    lines.append(f"Manifests checked: {report.manifest_count}")
    lines.append(f"Total checks run: {report.checks_run}")
    lines.append(f"Status: {'PASSED ✓' if report.passed else 'FAILED ✗'}")
    lines.append("")

    if report.failures:
        lines.append(f"FAILURES ({len(report.failures)}):")
        lines.append("-" * 60)
        for failure in report.failures:
            lines.append(
                f"  [{failure['manifest_id']}] {failure['check']}: {failure['message']}"
            )
        lines.append("")

    if report.warnings:
        lines.append(f"WARNINGS ({len(report.warnings)}):")
        lines.append("-" * 60)
        for warning in report.warnings:
            lines.append(
                f"  [{warning['manifest_id']}] {warning['check']}: {warning['message']}"
            )
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


def format_report_markdown(report: RentCheckReport) -> str:
    """Format report as markdown."""
    lines = []
    lines.append("# Rent Enforcement Report")
    lines.append("")
    lines.append(f"**Status**: {'PASSED ✓' if report.passed else 'FAILED ✗'}")
    lines.append(f"**Manifests Checked**: {report.manifest_count}")
    lines.append(f"**Total Checks Run**: {report.checks_run}")
    lines.append(f"**Timestamp**: {report.provenance.get('timestamp', 'N/A')}")
    lines.append("")

    if report.failures:
        lines.append(f"## Failures ({len(report.failures)})")
        lines.append("")
        for failure in report.failures:
            lines.append(
                f"- **[{failure['manifest_id']}]** `{failure['check']}`: {failure['message']}"
            )
        lines.append("")

    if report.warnings:
        lines.append(f"## Warnings ({len(report.warnings)})")
        lines.append("")
        for warning in report.warnings:
            lines.append(
                f"- **[{warning['manifest_id']}]** `{warning['check']}`: {warning['message']}"
            )
        lines.append("")

    return "\n".join(lines)
