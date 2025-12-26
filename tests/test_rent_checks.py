"""
Test Rent Checks

Tests for rent enforcement checks and gates.
"""

import pytest
from pathlib import Path
from abraxas.governance.rent_checks import (
    check_tests_exist,
    check_golden_files_declared,
    check_ledgers_declared,
    check_cost_model_present,
    check_operator_edges_declared,
    check_expected_cost_bounds,
    run_all_rent_checks,
    RentCheckReport,
    format_report_console,
    format_report_markdown,
)


@pytest.fixture
def repo_root():
    """Get repository root."""
    return str(Path(__file__).parent.parent)


@pytest.fixture
def valid_manifest():
    """Create a valid manifest for testing."""
    return {
        "id": "test_metric",
        "kind": "metric",
        "domain": "TAU",
        "description": "Test metric",
        "owner_module": "abraxas.metrics.test",
        "version": "0.1",
        "created_at": "2025-12-26",
        "inputs": ["input1"],
        "outputs": ["output1"],
        "cost_model": {
            "time_ms_expected": 50,
            "memory_kb_expected": 1024,
            "io_expected": "read",
        },
        "rent_claim": {
            "improves": ["auditability"],
            "measurable_by": ["golden_test"],
            "thresholds": {"accuracy_min": 0.9},
        },
        "proof": {
            "tests": ["tests/test_rent_checks.py::test_valid_manifest"],
            "golden_files": ["tests/golden/governance/example.json"],
            "ledgers_touched": ["out/ledgers/test.jsonl"],
        },
    }


def test_check_tests_exist_valid(valid_manifest, repo_root):
    """Test that existing test files pass the check."""
    errors = check_tests_exist(valid_manifest, repo_root)
    # This test file exists, so should pass
    assert len(errors) == 0


def test_check_tests_exist_missing(repo_root):
    """Test that missing test files fail the check."""
    manifest = {
        "proof": {
            "tests": ["tests/nonexistent_test.py::test_missing"],
        }
    }

    errors = check_tests_exist(manifest, repo_root)
    assert len(errors) > 0
    assert "does not exist" in errors[0]


def test_check_tests_exist_invalid_format(repo_root):
    """Test that invalid test format fails the check."""
    manifest = {
        "proof": {
            "tests": ["invalid_format"],
        }
    }

    errors = check_tests_exist(manifest, repo_root)
    assert len(errors) > 0
    assert "Invalid test format" in errors[0]


def test_check_golden_files_declared_with_tests(valid_manifest, repo_root):
    """Test that golden files are properly declared when tests exist."""
    warnings = check_golden_files_declared(valid_manifest, repo_root)
    # Valid manifest has both tests and golden files
    assert len(warnings) == 0


def test_check_golden_files_declared_missing(repo_root):
    """Test warning when tests exist but no golden files declared."""
    manifest = {
        "proof": {
            "tests": ["tests/test_example.py::test_something"],
            "golden_files": [],
        }
    }

    warnings = check_golden_files_declared(manifest, repo_root)
    assert len(warnings) > 0
    assert "no golden files" in warnings[0]


def test_check_ledgers_declared_valid(valid_manifest):
    """Test that properly declared ledgers pass."""
    warnings = check_ledgers_declared(valid_manifest)
    assert len(warnings) == 0


def test_check_ledgers_declared_empty():
    """Test warning when no ledgers declared."""
    manifest = {"proof": {"ledgers_touched": []}}

    warnings = check_ledgers_declared(manifest)
    assert len(warnings) > 0
    assert "No ledgers declared" in warnings[0]


def test_check_ledgers_declared_bad_extension():
    """Test warning for ledger files without .jsonl extension."""
    manifest = {"proof": {"ledgers_touched": ["out/ledgers/test.json"]}}

    warnings = check_ledgers_declared(manifest)
    assert len(warnings) > 0
    assert ".jsonl" in warnings[0]


def test_check_cost_model_present_valid(valid_manifest):
    """Test that valid cost model passes."""
    errors = check_cost_model_present(valid_manifest)
    assert len(errors) == 0


def test_check_cost_model_present_missing():
    """Test error when cost model is missing."""
    manifest = {}

    errors = check_cost_model_present(manifest)
    assert len(errors) > 0
    assert "Missing cost_model" in errors[0]


def test_check_cost_model_present_incomplete():
    """Test error when cost model is incomplete."""
    manifest = {"cost_model": {"time_ms_expected": 50}}  # Missing other fields

    errors = check_cost_model_present(manifest)
    assert len(errors) > 0


def test_check_operator_edges_declared_not_operator(valid_manifest):
    """Test that edge check is skipped for non-operator manifests."""
    errors = check_operator_edges_declared(valid_manifest)
    assert len(errors) == 0  # Not an operator, so no check


def test_check_operator_edges_declared_valid():
    """Test valid operator edges."""
    manifest = {
        "kind": "operator",
        "ter_edges_claimed": [{"from": "a", "to": "b"}],
    }

    errors = check_operator_edges_declared(manifest)
    # No TER spec provided, so just structural validation
    assert len(errors) == 0


def test_check_operator_edges_declared_invalid_with_spec():
    """Test invalid operator edges against TER spec."""
    manifest = {
        "kind": "operator",
        "ter_edges_claimed": [{"from": "x", "to": "y"}],
    }

    ter_spec = {"edges": [{"from": "a", "to": "b"}, {"from": "c", "to": "d"}]}

    errors = check_operator_edges_declared(manifest, ter_spec)
    assert len(errors) > 0
    assert "not in spec" in errors[0]


def test_check_expected_cost_bounds_no_stats(valid_manifest):
    """Test that cost bounds check is skipped when no stats available."""
    warnings = check_expected_cost_bounds(valid_manifest)
    assert len(warnings) == 0


def test_check_expected_cost_bounds_within_bounds(valid_manifest):
    """Test that costs within bounds pass."""
    observed_stats = {"time_ms_observed": 40, "memory_kb_observed": 800}

    warnings = check_expected_cost_bounds(valid_manifest, observed_stats)
    assert len(warnings) == 0


def test_check_expected_cost_bounds_exceeds_time(valid_manifest):
    """Test warning when observed time exceeds expected by >2x."""
    # Expected: 50ms, observed: 150ms (3x)
    observed_stats = {"time_ms_observed": 150, "memory_kb_observed": 800}

    warnings = check_expected_cost_bounds(valid_manifest, observed_stats)
    assert len(warnings) > 0
    assert "Observed time" in warnings[0]


def test_check_expected_cost_bounds_exceeds_memory(valid_manifest):
    """Test warning when observed memory exceeds expected by >2x."""
    # Expected: 1024KB, observed: 3072KB (3x)
    observed_stats = {"time_ms_observed": 40, "memory_kb_observed": 3072}

    warnings = check_expected_cost_bounds(valid_manifest, observed_stats)
    assert len(warnings) > 0
    assert "Observed memory" in warnings[0]


def test_run_all_rent_checks_empty(repo_root):
    """Test running checks on empty manifest set."""
    manifests = {"metrics": [], "operators": [], "artifacts": []}

    report = run_all_rent_checks(manifests, repo_root)

    assert report.passed is True
    assert report.manifest_count == 0
    assert len(report.failures) == 0


def test_run_all_rent_checks_valid_manifests(repo_root):
    """Test running checks on valid manifests."""
    manifests = {
        "metrics": [
            {
                "id": "test_metric",
                "kind": "metric",
                "proof": {
                    "tests": ["tests/test_rent_checks.py::test_valid_manifest"],
                    "golden_files": [],
                    "ledgers_touched": ["out/test.jsonl"],
                },
                "cost_model": {
                    "time_ms_expected": 10,
                    "memory_kb_expected": 100,
                    "io_expected": "none",
                },
            }
        ],
        "operators": [],
        "artifacts": [],
    }

    report = run_all_rent_checks(manifests, repo_root)

    assert report.manifest_count == 1
    assert report.checks_run > 0


def test_rent_check_report_add_failure():
    """Test adding failures to report."""
    report = RentCheckReport(passed=True)

    report.add_failure("test_id", "test_check", "Test failure message")

    assert report.passed is False
    assert len(report.failures) == 1
    assert report.failures[0]["manifest_id"] == "test_id"
    assert report.failures[0]["check"] == "test_check"


def test_rent_check_report_add_warning():
    """Test adding warnings to report."""
    report = RentCheckReport(passed=True)

    report.add_warning("test_id", "test_check", "Test warning message")

    assert report.passed is True  # Warnings don't fail
    assert len(report.warnings) == 1
    assert report.warnings[0]["manifest_id"] == "test_id"


def test_rent_check_report_to_dict():
    """Test converting report to dict."""
    report = RentCheckReport(passed=True, manifest_count=5, checks_run=20)
    report.add_failure("m1", "check1", "error1")
    report.add_warning("m2", "check2", "warning1")

    data = report.to_dict()

    assert data["passed"] is False  # Has failures
    assert data["manifest_count"] == 5
    assert data["checks_run"] == 20
    assert len(data["failures"]) == 1
    assert len(data["warnings"]) == 1


def test_format_report_console():
    """Test console report formatting."""
    report = RentCheckReport(passed=True, manifest_count=3, checks_run=12)
    report.add_failure("m1", "tests_exist", "Test file missing")

    output = format_report_console(report)

    assert "RENT ENFORCEMENT REPORT" in output
    assert "Manifests checked: 3" in output
    assert "Total checks run: 12" in output
    assert "FAILED" in output
    assert "m1" in output


def test_format_report_markdown():
    """Test markdown report formatting."""
    report = RentCheckReport(passed=True, manifest_count=2, checks_run=8)
    report.add_warning("m1", "ledgers_declared", "No ledgers")

    output = format_report_markdown(report)

    assert "# Rent Enforcement Report" in output
    assert "**Manifests Checked**: 2" in output
    assert "## Warnings" in output
    assert "m1" in output
