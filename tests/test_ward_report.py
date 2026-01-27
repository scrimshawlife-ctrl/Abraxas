"""
Tests for WardReport.v0 and WardFlag.v0

Verifies:
- Deterministic hashing
- Validation invariants
- Semantic equality
- Governance flag constraints
"""

import pytest

from abx_familiar.ir import (
    WardFlag,
    WardReport,
    DRIFT_CLASSES,
)


# -------------------------
# WardFlag Fixtures
# -------------------------

@pytest.fixture
def error_flag():
    """An error severity WardFlag."""
    return WardFlag(
        code="TIER_LEAKAGE",
        message="Enterprise data accessed from Psychonaut tier",
        severity="error",
        meta={"tier_from": "Psychonaut", "tier_to": "Enterprise"},
    )


@pytest.fixture
def warn_flag():
    """A warning severity WardFlag."""
    return WardFlag(
        code="BUDGET_EXCEEDED",
        message="Compute budget exceeded by 15%",
        severity="warn",
        meta={"budget": 100, "actual": 115},
    )


@pytest.fixture
def info_flag():
    """An info severity WardFlag."""
    return WardFlag(
        code="INVARIANCE_CHECK",
        message="Invariance check completed successfully",
        severity="info",
    )


# -------------------------
# WardReport Fixtures
# -------------------------

@pytest.fixture
def report_with_violations(error_flag, warn_flag):
    """A WardReport with violations and warnings."""
    return WardReport(
        report_id="WARD-001",
        violations=[error_flag],
        warnings=[warn_flag],
        tier_leakage_flags=["TIER_LEAKAGE"],
        drift_class="structural",
        invariance_passed=False,
    )


@pytest.fixture
def clean_report():
    """A clean WardReport with no issues."""
    return WardReport(
        report_id="WARD-002",
        violations=[],
        warnings=[],
        drift_class="none",
        invariance_passed=True,
    )


@pytest.fixture
def minimal_report():
    """A minimal WardReport with defaults."""
    return WardReport(
        report_id="WARD-003",
    )


# -------------------------
# WardFlag Validation Tests
# -------------------------

class TestWardFlagValidation:
    """Tests for WardFlag validation."""

    def test_valid_error_flag(self, error_flag):
        """Valid error flag should pass validation."""
        error_flag.validate()  # Should not raise

    def test_valid_warn_flag(self, warn_flag):
        """Valid warning flag should pass validation."""
        warn_flag.validate()  # Should not raise

    def test_valid_info_flag(self, info_flag):
        """Valid info flag should pass validation."""
        info_flag.validate()  # Should not raise

    def test_empty_code_raises(self):
        """Empty code should raise ValueError."""
        flag = WardFlag(
            code="",
            message="Some message",
            severity="error",
        )
        with pytest.raises(ValueError, match="code must be non-empty"):
            flag.validate()

    def test_empty_message_raises(self):
        """Empty message should raise ValueError."""
        flag = WardFlag(
            code="SOME_CODE",
            message="",
            severity="error",
        )
        with pytest.raises(ValueError, match="message must be non-empty"):
            flag.validate()

    def test_empty_severity_raises(self):
        """Empty severity should raise ValueError."""
        flag = WardFlag(
            code="SOME_CODE",
            message="Some message",
            severity="",
        )
        with pytest.raises(ValueError, match="severity must be non-empty"):
            flag.validate()

    def test_custom_severity_valid(self):
        """Custom severity values should be valid (no enum restriction)."""
        flag = WardFlag(
            code="CUSTOM",
            message="Custom severity test",
            severity="custom_level",
        )
        flag.validate()  # Should not raise


# -------------------------
# WardFlag Payload Tests
# -------------------------

class TestWardFlagPayload:
    """Tests for WardFlag payload conversion."""

    def test_to_payload_returns_dict(self, error_flag):
        """WardFlag.to_payload should return a dictionary."""
        payload = error_flag.to_payload()
        assert isinstance(payload, dict)

    def test_payload_contains_all_fields(self, error_flag):
        """Payload should contain all fields."""
        payload = error_flag.to_payload()
        expected_keys = {"code", "message", "severity", "meta"}
        assert set(payload.keys()) == expected_keys

    def test_payload_values_match(self, error_flag):
        """Payload values should match flag fields."""
        payload = error_flag.to_payload()
        assert payload["code"] == error_flag.code
        assert payload["message"] == error_flag.message
        assert payload["severity"] == error_flag.severity
        assert payload["meta"] == error_flag.meta


# -------------------------
# WardReport Validation Tests
# -------------------------

class TestWardReportValidation:
    """Tests for WardReport validation."""

    def test_valid_report_with_violations(self, report_with_violations):
        """Report with violations should pass validation."""
        report_with_violations.validate()  # Should not raise

    def test_valid_clean_report(self, clean_report):
        """Clean report should pass validation."""
        clean_report.validate()  # Should not raise

    def test_valid_minimal_report(self, minimal_report):
        """Minimal report with defaults should pass validation."""
        minimal_report.validate()  # Should not raise

    def test_invalid_drift_class_raises(self):
        """Invalid drift_class should raise ValueError."""
        report = WardReport(
            report_id="WARD-ERR",
            drift_class="invalid_drift",
        )
        with pytest.raises(ValueError, match="Invalid drift_class"):
            report.validate()

    def test_all_drift_classes_valid(self):
        """All defined DRIFT_CLASSES should be valid."""
        for drift in DRIFT_CLASSES:
            report = WardReport(
                report_id="TEST",
                drift_class=drift,
            )
            report.validate()  # Should not raise

    def test_violations_must_be_ward_flags(self):
        """Violations must be WardFlag objects."""
        report = WardReport(
            report_id="WARD-ERR",
            violations=[{"code": "NOT_A_FLAG"}],  # type: ignore
        )
        with pytest.raises(ValueError, match="WardFlag objects"):
            report.validate()

    def test_warnings_must_be_ward_flags(self):
        """Warnings must be WardFlag objects."""
        report = WardReport(
            report_id="WARD-ERR",
            warnings=[{"code": "NOT_A_FLAG"}],  # type: ignore
        )
        with pytest.raises(ValueError, match="WardFlag objects"):
            report.validate()

    def test_invalid_violation_flag_propagates(self):
        """Invalid flag in violations should cause validation to fail."""
        invalid_flag = WardFlag(
            code="",  # Invalid - empty
            message="Test",
            severity="error",
        )
        report = WardReport(
            report_id="WARD-ERR",
            violations=[invalid_flag],
        )
        with pytest.raises(ValueError, match="code must be non-empty"):
            report.validate()

    def test_invalid_warning_flag_propagates(self):
        """Invalid flag in warnings should cause validation to fail."""
        invalid_flag = WardFlag(
            code="TEST",
            message="",  # Invalid - empty
            severity="warn",
        )
        report = WardReport(
            report_id="WARD-ERR",
            warnings=[invalid_flag],
        )
        with pytest.raises(ValueError, match="message must be non-empty"):
            report.validate()

    def test_not_computable_without_missing_fields_raises(self):
        """not_computable=True without missing_fields should raise."""
        report = WardReport(
            report_id="WARD-ERR",
            not_computable=True,
            missing_fields=[],
        )
        with pytest.raises(ValueError, match="missing_fields to be non-empty"):
            report.validate()

    def test_invariance_passed_none_valid(self):
        """invariance_passed=None (not executed) should be valid."""
        report = WardReport(
            report_id="WARD-TEST",
            invariance_passed=None,
        )
        report.validate()  # Should not raise

    def test_invariance_passed_true_valid(self):
        """invariance_passed=True should be valid."""
        report = WardReport(
            report_id="WARD-TEST",
            invariance_passed=True,
        )
        report.validate()  # Should not raise

    def test_invariance_passed_false_valid(self):
        """invariance_passed=False should be valid."""
        report = WardReport(
            report_id="WARD-TEST",
            invariance_passed=False,
        )
        report.validate()  # Should not raise


# -------------------------
# WardReport Hashing Tests
# -------------------------

class TestWardReportHashing:
    """Tests for WardReport deterministic hashing."""

    def test_hash_is_deterministic(self, report_with_violations):
        """Same report should produce same hash."""
        hash1 = report_with_violations.hash()
        hash2 = report_with_violations.hash()
        assert hash1 == hash2

    def test_hash_is_sha256(self, report_with_violations):
        """Hash should be a valid SHA-256 hex string."""
        h = report_with_violations.hash()
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_equivalent_reports_same_hash(self, error_flag):
        """Two reports with identical content should have same hash."""
        report1 = WardReport(
            report_id="WARD-X",
            violations=[error_flag],
            drift_class="benign",
        )
        # Create identical flag
        flag_copy = WardFlag(
            code=error_flag.code,
            message=error_flag.message,
            severity=error_flag.severity,
            meta=dict(error_flag.meta),
        )
        report2 = WardReport(
            report_id="WARD-X",
            violations=[flag_copy],
            drift_class="benign",
        )
        assert report1.hash() == report2.hash()

    def test_different_report_id_different_hash(self, report_with_violations, error_flag, warn_flag):
        """Different report_id should produce different hash."""
        report2 = WardReport(
            report_id="DIFFERENT-ID",
            violations=[error_flag],
            warnings=[warn_flag],
            tier_leakage_flags=["TIER_LEAKAGE"],
            drift_class="structural",
            invariance_passed=False,
        )
        assert report_with_violations.hash() != report2.hash()

    def test_violation_order_matters(self, error_flag, warn_flag):
        """Violation order should affect hash."""
        # Convert warn_flag to error severity for this test
        flag1 = WardFlag(code="A", message="First", severity="error")
        flag2 = WardFlag(code="B", message="Second", severity="error")

        report1 = WardReport(
            report_id="WARD",
            violations=[flag1, flag2],
        )
        report2 = WardReport(
            report_id="WARD",
            violations=[flag2, flag1],
        )
        assert report1.hash() != report2.hash()

    def test_meta_order_irrelevant_for_hash(self):
        """Meta dict order should not affect hash (canonical JSON sorting)."""
        flag1 = WardFlag(
            code="TEST",
            message="Test",
            severity="info",
            meta={"z": 1, "a": 2},
        )
        flag2 = WardFlag(
            code="TEST",
            message="Test",
            severity="info",
            meta={"a": 2, "z": 1},
        )
        report1 = WardReport(report_id="R", violations=[flag1])
        report2 = WardReport(report_id="R", violations=[flag2])
        assert report1.hash() == report2.hash()


# -------------------------
# WardReport Semantic Equality Tests
# -------------------------

class TestWardReportSemanticEquality:
    """Tests for semantic equality."""

    def test_identical_reports_semantically_equal(self, error_flag):
        """Two reports with identical content should be semantically equal."""
        report1 = WardReport(
            report_id="WARD-X",
            violations=[error_flag],
        )
        flag_copy = WardFlag(
            code=error_flag.code,
            message=error_flag.message,
            severity=error_flag.severity,
            meta=dict(error_flag.meta),
        )
        report2 = WardReport(
            report_id="WARD-X",
            violations=[flag_copy],
        )
        assert report1.semantically_equal(report2)
        assert report2.semantically_equal(report1)

    def test_different_reports_not_semantically_equal(self, report_with_violations, clean_report):
        """Different reports should not be semantically equal."""
        assert not report_with_violations.semantically_equal(clean_report)

    def test_semantically_equal_with_non_report_returns_false(self, report_with_violations):
        """Comparing with non-report should return False."""
        assert not report_with_violations.semantically_equal("not a report")
        assert not report_with_violations.semantically_equal(None)
        assert not report_with_violations.semantically_equal({"report_id": "WARD-001"})


# -------------------------
# Payload Tests
# -------------------------

class TestPayload:
    """Tests for payload conversion."""

    def test_report_to_payload_returns_dict(self, report_with_violations):
        """WardReport.to_payload should return a dictionary."""
        payload = report_with_violations.to_payload()
        assert isinstance(payload, dict)

    def test_report_payload_contains_all_fields(self, report_with_violations):
        """Report payload should contain all fields."""
        payload = report_with_violations.to_payload()
        expected_keys = {
            "report_id",
            "violations",
            "warnings",
            "tier_leakage_flags",
            "drift_class",
            "invariance_passed",
            "not_computable",
            "missing_fields",
        }
        assert set(payload.keys()) == expected_keys

    def test_payload_violations_are_dicts(self, report_with_violations):
        """Payload violations should be converted to dicts."""
        payload = report_with_violations.to_payload()
        assert all(isinstance(v, dict) for v in payload["violations"])

    def test_payload_warnings_are_dicts(self, report_with_violations):
        """Payload warnings should be converted to dicts."""
        payload = report_with_violations.to_payload()
        assert all(isinstance(w, dict) for w in payload["warnings"])


# -------------------------
# Edge Cases
# -------------------------

class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_report_id_valid(self):
        """Empty report_id should be allowed."""
        report = WardReport(report_id="")
        report.validate()  # Should not raise

    def test_many_violations(self):
        """Report with many violations should hash correctly."""
        violations = [
            WardFlag(
                code=f"CODE_{i}",
                message=f"Message {i}",
                severity="error",
            )
            for i in range(100)
        ]
        report = WardReport(
            report_id="WARD-LARGE",
            violations=violations,
        )
        h = report.hash()
        assert len(h) == 64

    def test_unicode_in_fields(self):
        """Unicode content should hash correctly."""
        flag = WardFlag(
            code="UNICODE_\u4e2d\u6587",
            message="Message with \u00e9\u00e8\u00ea",
            severity="info",
        )
        report = WardReport(
            report_id="WARD-\U0001f600",
            violations=[flag],
        )
        h = report.hash()
        assert len(h) == 64

    def test_nested_meta(self):
        """Nested meta dict should hash correctly."""
        flag = WardFlag(
            code="NESTED",
            message="Nested meta test",
            severity="info",
            meta={
                "nested": {
                    "deep": {"value": 123}
                }
            },
        )
        report = WardReport(
            report_id="WARD-NESTED",
            violations=[flag],
        )
        h = report.hash()
        assert len(h) == 64

    def test_special_json_values_in_meta(self):
        """Special JSON values should serialize correctly."""
        flag = WardFlag(
            code="SPECIAL",
            message="Special values test",
            severity="info",
            meta={
                "null_value": None,
                "bool_true": True,
                "bool_false": False,
                "float_value": 3.14159,
                "int_value": 42,
            },
        )
        report = WardReport(
            report_id="WARD-SPECIAL",
            violations=[flag],
        )
        h = report.hash()
        assert len(h) == 64

    def test_critical_drift_with_violations(self):
        """Critical drift with violations should validate."""
        flag = WardFlag(
            code="CRITICAL_ISSUE",
            message="Critical drift detected",
            severity="error",
        )
        report = WardReport(
            report_id="WARD-CRITICAL",
            violations=[flag],
            drift_class="critical",
            invariance_passed=False,
        )
        report.validate()  # Should not raise
        assert len(report.hash()) == 64

    def test_tier_leakage_flags_list(self):
        """tier_leakage_flags should accept string list."""
        report = WardReport(
            report_id="WARD-LEAKAGE",
            tier_leakage_flags=["LEAK_1", "LEAK_2", "LEAK_3"],
        )
        report.validate()  # Should not raise
        payload = report.to_payload()
        assert payload["tier_leakage_flags"] == ["LEAK_1", "LEAK_2", "LEAK_3"]
