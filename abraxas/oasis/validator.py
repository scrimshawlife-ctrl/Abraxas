"""OAS Validator: validates operator candidates against held-out data."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from abraxas.core.metrics import compute_entropy, compute_false_classification_rate
from abraxas.core.provenance import ProvenanceBundle, ProvenanceRef, hash_canonical_json
from abraxas.core.resonance_frame import ResonanceFrame
from abraxas.oasis.models import OperatorCandidate, ValidationReport
from abraxas.slang.operators.base import Operator


class OASValidator:
    """
    Validates operator candidates.

    Evaluates candidates against held-out data and computes metrics.
    """

    def __init__(
        self,
        min_entropy_delta: float = -0.05,
        min_false_cringe_delta: float = -0.10,
        holdout_ratio: float = 0.2,
    ):
        """
        Initialize validator.

        Args:
            min_entropy_delta: Minimum entropy improvement (negative = better)
            min_false_cringe_delta: Minimum false classification improvement
            holdout_ratio: Ratio of data to hold out for validation
        """
        self.min_entropy_delta = min_entropy_delta
        self.min_false_cringe_delta = min_false_cringe_delta
        self.holdout_ratio = holdout_ratio

    def validate(
        self,
        candidate: OperatorCandidate,
        frames: list[ResonanceFrame],
        existing_operators: list[Operator],
    ) -> ValidationReport:
        """
        Validate a candidate operator.

        Splits data deterministically, evaluates before/after metrics.
        """
        # Deterministic holdout split based on event_id hash
        train_frames, test_frames = self._split_frames(frames)

        # Compute baseline metrics (without candidate)
        metrics_before = self._compute_metrics(test_frames, existing_operators)

        # Simulate adding candidate and recompute
        # For now, we'll use a simple simulation since we can't dynamically instantiate
        metrics_after = self._simulate_with_candidate(
            test_frames, existing_operators, candidate
        )

        # Compute deltas
        deltas = {
            key: metrics_after.get(key, 0.0) - metrics_before.get(key, 0.0)
            for key in set(metrics_before.keys()) | set(metrics_after.keys())
        }

        # Check if validation passes
        passed = self._check_validation_criteria(deltas)

        notes = []
        if passed:
            notes.append("Candidate meets validation criteria")
        else:
            notes.append("Candidate does not meet validation criteria")

        # Build provenance
        provenance = ProvenanceBundle(
            inputs=[
                ProvenanceRef(
                    scheme="candidate",
                    path=candidate.operator_id,
                    sha256=hash_canonical_json(candidate.model_dump()),
                )
            ],
            transforms=["validation", "metric_computation"],
            metrics=deltas,
            created_by="oasis_validator",
        )

        report = ValidationReport(
            passed=passed,
            metrics_before=metrics_before,
            metrics_after=metrics_after,
            deltas=deltas,
            notes=notes,
            provenance=provenance,
        )

        return report

    def _split_frames(
        self, frames: list[ResonanceFrame]
    ) -> tuple[list[ResonanceFrame], list[ResonanceFrame]]:
        """Deterministically split frames into train/test."""
        # Hash-based split for determinism
        test_frames = []
        train_frames = []

        for frame in frames:
            hash_val = int(hashlib.md5(frame.event_id.encode()).hexdigest(), 16)
            if (hash_val % 100) < (self.holdout_ratio * 100):
                test_frames.append(frame)
            else:
                train_frames.append(frame)

        return train_frames, test_frames

    def _compute_metrics(
        self, frames: list[ResonanceFrame], operators: list[Operator]
    ) -> dict[str, float]:
        """Compute metrics on frames with given operators."""
        predictions = []
        ground_truth = []

        for frame in frames:
            # Apply operators
            pred = None
            for op in operators:
                readout = op.apply(frame.text, frame)
                if readout:
                    pred = readout.label
                    break

            predictions.append(pred)

            # Ground truth: use a simple heuristic (in production, would be labeled data)
            # For now, mark anything with known patterns as "known"
            if self._has_known_patterns(frame.text):
                ground_truth.append("known")
            else:
                ground_truth.append("unknown")

        # Compute metrics
        entropy = compute_entropy(predictions)
        false_rate = compute_false_classification_rate(predictions, ground_truth)

        return {"entropy": entropy, "false_classification_rate": false_rate}

    def _simulate_with_candidate(
        self,
        frames: list[ResonanceFrame],
        operators: list[Operator],
        candidate: OperatorCandidate,
    ) -> dict[str, float]:
        """Simulate metrics with candidate added (simplified)."""
        predictions = []
        ground_truth = []

        for frame in frames:
            # Try candidate first
            pred = None

            # Simulate candidate application
            if self._candidate_matches(frame.text, candidate):
                pred = candidate.readouts[0] if candidate.readouts else "candidate_match"
            else:
                # Try existing operators
                for op in operators:
                    readout = op.apply(frame.text, frame)
                    if readout:
                        pred = readout.label
                        break

            predictions.append(pred)

            # Ground truth (same as before)
            if self._has_known_patterns(frame.text):
                ground_truth.append("known")
            else:
                ground_truth.append("unknown")

        # Compute metrics
        entropy = compute_entropy(predictions)
        false_rate = compute_false_classification_rate(predictions, ground_truth)

        return {"entropy": entropy, "false_classification_rate": false_rate}

    def _candidate_matches(self, text: str, candidate: OperatorCandidate) -> bool:
        """Check if candidate triggers would match text."""
        for trigger in candidate.triggers:
            try:
                if re.search(trigger, text, re.IGNORECASE):
                    return True
            except re.error:
                # Invalid regex, skip
                pass
        return False

    def _has_known_patterns(self, text: str) -> bool:
        """Check if text has known patterns (heuristic for ground truth)."""
        known_patterns = [
            r"\b(rawr|raar|nyaa|uwu|owo)\b",
            r"[xX][dD]",
            r"[:;][3pP]",
            r"\b(lol|lmao)\b",
        ]
        for pattern in known_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _check_validation_criteria(self, deltas: dict[str, float]) -> bool:
        """Check if deltas meet validation criteria."""
        entropy_delta = deltas.get("entropy", 0.0)
        false_rate_delta = deltas.get("false_classification_rate", 0.0)

        # Both should improve (be negative)
        entropy_ok = entropy_delta <= self.min_entropy_delta
        false_rate_ok = false_rate_delta <= self.min_false_cringe_delta

        return entropy_ok and false_rate_ok
