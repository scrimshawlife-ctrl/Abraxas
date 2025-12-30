"""
Tests for Lane Guard.

Validates:
1. Lane separation enforcement
2. Promotion record validation
3. Forbidden criteria rejection
4. Provenance tracking
"""

import pytest
import tempfile
import json
from pathlib import Path
from abraxas.detectors.shadow.lane_guard import (
    LaneGuard,
    LaneViolationError,
    PromotionRecord,
)


def serialize_promotion_record(record: PromotionRecord) -> str:
    """Helper to serialize PromotionRecord to JSON string."""
    return json.dumps(record.model_dump())


class TestPromotionRecord:
    """Tests for PromotionRecord validation."""

    def test_valid_promotion(self):
        """Test that valid promotion record is accepted."""
        record = PromotionRecord(
            metric_name="test_metric",
            status="PROMOTED",
            promotion_date="2025-01-01T00:00:00Z",
            calibration_score=0.85,
            stability_score=0.90,
            redundancy_score=0.75,
            promotion_hash="abc123",
        )

        assert record.metric_name == "test_metric"
        assert record.status == "PROMOTED"

    def test_forbidden_ethical_score(self):
        """Test that ethical_score is forbidden."""
        with pytest.raises(ValueError, match="FORBIDDEN.*ethical_score"):
            PromotionRecord(
                metric_name="test_metric",
                status="PROMOTED",
                promotion_date="2025-01-01T00:00:00Z",
                calibration_score=0.85,
                stability_score=0.90,
                redundancy_score=0.75,
                promotion_hash="abc123",
                ethical_score=0.5,  # FORBIDDEN
            )

    def test_forbidden_risk_score(self):
        """Test that risk_score is forbidden."""
        with pytest.raises(ValueError, match="FORBIDDEN.*risk_score"):
            PromotionRecord(
                metric_name="test_metric",
                status="PROMOTED",
                promotion_date="2025-01-01T00:00:00Z",
                calibration_score=0.85,
                stability_score=0.90,
                redundancy_score=0.75,
                promotion_hash="abc123",
                risk_score=0.3,  # FORBIDDEN
            )

    def test_forbidden_diagnostic_only(self):
        """Test that diagnostic_only is forbidden."""
        with pytest.raises(ValueError, match="FORBIDDEN.*diagnostic_only"):
            PromotionRecord(
                metric_name="test_metric",
                status="PROMOTED",
                promotion_date="2025-01-01T00:00:00Z",
                calibration_score=0.85,
                stability_score=0.90,
                redundancy_score=0.75,
                promotion_hash="abc123",
                diagnostic_only=True,  # FORBIDDEN
            )


class TestLaneGuard:
    """Tests for LaneGuard enforcement."""

    def test_empty_ledger(self):
        """Test that empty ledger rejects all metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "promotion_ledger.jsonl"
            guard = LaneGuard(promotion_ledger_path=str(ledger_path))

            with pytest.raises(LaneViolationError, match="shadow metric"):
                guard.check_promotion("compliance_remix")

    def test_promoted_metric_allowed(self):
        """Test that promoted metric is allowed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "promotion_ledger.jsonl"

            # Create ledger with promoted metric
            record = PromotionRecord(
                metric_name="compliance_remix",
                status="PROMOTED",
                promotion_date="2025-01-01T00:00:00Z",
                calibration_score=0.85,
                stability_score=0.90,
                redundancy_score=0.75,
                promotion_hash="abc123",
            )

            with open(ledger_path, 'w') as f:
                f.write(serialize_promotion_record(record) + "\n")

            guard = LaneGuard(promotion_ledger_path=str(ledger_path))

            # Should not raise
            result = guard.check_promotion("compliance_remix")
            assert result.metric_name == "compliance_remix"

    def test_rejected_metric_blocked(self):
        """Test that rejected metric is blocked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "promotion_ledger.jsonl"

            # Create ledger with rejected metric
            record = PromotionRecord(
                metric_name="compliance_remix",
                status="REJECTED",
                promotion_date="2025-01-01T00:00:00Z",
                calibration_score=0.45,
                stability_score=0.50,
                redundancy_score=0.40,
                promotion_hash="abc123",
            )

            with open(ledger_path, 'w') as f:
                f.write(serialize_promotion_record(record) + "\n")

            guard = LaneGuard(promotion_ledger_path=str(ledger_path))

            # Should raise because status is REJECTED
            with pytest.raises(LaneViolationError):
                guard.check_promotion("compliance_remix")

    def test_is_promoted(self):
        """Test is_promoted check (non-raising)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "promotion_ledger.jsonl"

            record = PromotionRecord(
                metric_name="compliance_remix",
                status="PROMOTED",
                promotion_date="2025-01-01T00:00:00Z",
                calibration_score=0.85,
                stability_score=0.90,
                redundancy_score=0.75,
                promotion_hash="abc123",
            )

            with open(ledger_path, 'w') as f:
                f.write(serialize_promotion_record(record) + "\n")

            guard = LaneGuard(promotion_ledger_path=str(ledger_path))

            assert guard.is_promoted("compliance_remix") is True
            assert guard.is_promoted("meta_awareness") is False

    def test_get_all_promoted(self):
        """Test getting list of all promoted metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "promotion_ledger.jsonl"

            # Create ledger with multiple promoted metrics
            records = [
                PromotionRecord(
                    metric_name="compliance_remix",
                    status="PROMOTED",
                    promotion_date="2025-01-01T00:00:00Z",
                    calibration_score=0.85,
                    stability_score=0.90,
                    redundancy_score=0.75,
                    promotion_hash="abc123",
                ),
                PromotionRecord(
                    metric_name="meta_awareness",
                    status="PROMOTED",
                    promotion_date="2025-01-02T00:00:00Z",
                    calibration_score=0.80,
                    stability_score=0.85,
                    redundancy_score=0.70,
                    promotion_hash="def456",
                ),
                PromotionRecord(
                    metric_name="negative_space",
                    status="REJECTED",
                    promotion_date="2025-01-03T00:00:00Z",
                    calibration_score=0.50,
                    stability_score=0.55,
                    redundancy_score=0.45,
                    promotion_hash="ghi789",
                ),
            ]

            with open(ledger_path, 'w') as f:
                for record in records:
                    f.write(serialize_promotion_record(record) + "\n")

            guard = LaneGuard(promotion_ledger_path=str(ledger_path))

            promoted = guard.get_all_promoted()

            # Should only include PROMOTED status
            assert len(promoted) == 2
            assert "compliance_remix" in promoted
            assert "meta_awareness" in promoted
            assert "negative_space" not in promoted

    def test_validate_promotion_criteria(self):
        """Test explicit validation of promotion criteria."""
        guard = LaneGuard()

        # Valid record
        valid_record = PromotionRecord(
            metric_name="test_metric",
            status="PROMOTED",
            promotion_date="2025-01-01T00:00:00Z",
            calibration_score=0.85,
            stability_score=0.90,
            redundancy_score=0.75,
            promotion_hash="abc123",
        )

        # Should not raise
        guard.validate_promotion_criteria(valid_record)
