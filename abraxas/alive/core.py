"""
ALIVE Engine - Core computation entry point.

IMPORTANT: This module is intentionally DUMB at this stage.
It proves the plumbing works before intelligence exists.

The core entrypoint is alive_run():
    artifact → field signature (shape-correct, placeholder math)
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from typing import Any, Optional

from abraxas.alive.models import (
    ALIVEArtifact,
    ALIVEFieldSignature,
    ALIVEProfile,
    ALIVERunInput,
    CompositeScore,
    CorpusProvenance,
    InfluenceMetric,
    LifeLogisticsMetric,
    MetricStatus,
    MetricStrain,
    VitalityMetric,
)


# ═══════════════════════════════════════════════════════════════════════════
# CORE ENTRYPOINT: alive_run()
# ═══════════════════════════════════════════════════════════════════════════


def alive_run(
    artifact: ALIVEArtifact | dict,
    tier: str,
    profile: ALIVEProfile | dict | None = None,
) -> dict:
    """
    ALIVE core entrypoint: accepts artifact, returns field signature.

    This is INTENTIONALLY DUMB. It proves plumbing before intelligence.

    Args:
        artifact: Normalized text/media object
        tier: "psychonaut" | "academic" | "enterprise"
        profile: Onboarding-derived weights (optional)

    Returns:
        ALIVE Field Signature as dict (shape-correct, placeholder math)
    """
    # Normalize inputs
    if isinstance(artifact, dict):
        artifact = ALIVEArtifact(**artifact)
    if profile is None:
        profile = ALIVEProfile(profileId="default")
    elif isinstance(profile, dict):
        profile = ALIVEProfile(**profile)

    # Generate analysis ID (deterministic)
    analysis_id = _generate_analysis_id(artifact, tier)

    # Generate placeholder field signature (STUB)
    field_signature = _generate_stub_field_signature(
        analysis_id=analysis_id,
        artifact=artifact,
        tier=tier,
        profile=profile,
    )

    # Return as dict
    return field_signature.model_dump(mode="json")


def _generate_analysis_id(artifact: ALIVEArtifact, tier: str) -> str:
    """Generate deterministic analysis ID."""
    now = datetime.now(timezone.utc).isoformat()
    payload = f"{artifact.artifactId}:{tier}:{now}"
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _generate_stub_field_signature(
    analysis_id: str,
    artifact: ALIVEArtifact,
    tier: str,
    profile: ALIVEProfile,
) -> ALIVEFieldSignature:
    """
    Generate stub field signature with correct shape.

    PLACEHOLDER MATH ONLY. Shape correctness, not intelligence.
    """
    now = datetime.now(timezone.utc)

    # Stub influence metrics
    influence_metrics = [
        InfluenceMetric(
            metricId="influence.network_position",
            metricVersion="1.0.0",
            status=MetricStatus.PROMOTED,
            value=0.65,
            confidence=0.8,
            timestamp=now,
        ),
        InfluenceMetric(
            metricId="influence.persuasive_reach",
            metricVersion="1.0.0",
            status=MetricStatus.PROMOTED,
            value=0.72,
            confidence=0.75,
            timestamp=now,
        ),
    ]

    # Stub vitality metrics
    vitality_metrics = [
        VitalityMetric(
            metricId="vitality.creative_momentum",
            metricVersion="1.0.0",
            status=MetricStatus.PROMOTED,
            value=0.58,
            confidence=0.7,
            timestamp=now,
        ),
        VitalityMetric(
            metricId="vitality.discourse_velocity",
            metricVersion="1.0.0",
            status=MetricStatus.PROMOTED,
            value=0.82,
            confidence=0.85,
            timestamp=now,
        ),
        VitalityMetric(
            metricId="vitality.engagement_coherence",
            metricVersion="1.0.0",
            status=MetricStatus.PROMOTED,
            value=0.69,
            confidence=0.8,
            timestamp=now,
        ),
    ]

    # Stub life-logistics metrics
    life_logistics_metrics = [
        LifeLogisticsMetric(
            metricId="life_logistics.time_debt",
            metricVersion="1.0.0",
            status=MetricStatus.PROMOTED,
            value=0.45,  # Inverted: lower is better
            confidence=0.65,
            timestamp=now,
        ),
        LifeLogisticsMetric(
            metricId="life_logistics.material_runway",
            metricVersion="1.0.0",
            status=MetricStatus.PROMOTED,
            value=0.55,
            confidence=0.7,
            timestamp=now,
        ),
        LifeLogisticsMetric(
            metricId="life_logistics.operational_friction",
            metricVersion="1.0.0",
            status=MetricStatus.PROMOTED,
            value=0.38,  # Inverted: lower is better
            confidence=0.6,
            timestamp=now,
        ),
    ]

    # Stub composite score (using profile weights)
    composite = CompositeScore(
        overall=0.62,
        influenceWeight=profile.influenceWeight,
        vitalityWeight=profile.vitalityWeight,
        lifeLogisticsWeight=profile.lifeLogisticsWeight,
    )

    # Stub corpus provenance
    provenance = [
        CorpusProvenance(
            sourceId=artifact.artifactId,
            sourceType=artifact.artifactType,
            weight=1.0,
            timestamp=now,
        ),
    ]

    # Metric strain (academic tier only)
    metric_strain = None
    if tier == "academic":
        metric_strain = MetricStrain(
            detected=False,
            strainReport=None,
        )

    return ALIVEFieldSignature(
        analysisId=analysis_id,
        subjectId=artifact.artifactId,
        timestamp=now,
        influence=influence_metrics,
        vitality=vitality_metrics,
        lifeLogistics=life_logistics_metrics,
        compositeScore=composite,
        corpusProvenance=provenance,
        metricStrain=metric_strain,
    )


# ═══════════════════════════════════════════════════════════════════════════
# LEGACY WRAPPER (for backward compatibility)
# ═══════════════════════════════════════════════════════════════════════════


class ALIVEEngine:
    """
    ALIVE: Autonomous Life-Influence Vitality Engine

    This class wraps alive_run() for compatibility with existing code.
    New code should call alive_run() directly.
    """

    def __init__(self, registry_path: str | None = None):
        """
        Initialize ALIVE engine.

        Args:
            registry_path: Path to metric registry (optional for now)
        """
        self.registry_path = registry_path

    def run(self, input_data: ALIVERunInput | dict) -> ALIVEFieldSignature:
        """
        Run ALIVE analysis and return field signature.

        Args:
            input_data: ALIVERunInput or dict with analysis parameters

        Returns:
            ALIVEFieldSignature with computed metrics
        """
        # Normalize input
        if isinstance(input_data, dict):
            input_data = ALIVERunInput(**input_data)

        # Create artifact from input (temporary until we refactor to artifact-first)
        artifact = ALIVEArtifact(
            artifactId=input_data.subjectId,
            artifactType="text",
            content=f"Placeholder content for {input_data.subjectId}",
        )

        # Call alive_run
        result = alive_run(artifact, input_data.tier, profile=None)

        # Return as model
        return ALIVEFieldSignature(**result)


# ═══════════════════════════════════════════════════════════════════════════
# CLI ENTRYPOINT (for testing)
# ═══════════════════════════════════════════════════════════════════════════


def main():
    """CLI entrypoint for testing alive_run()."""
    if len(sys.argv) < 2:
        print("Usage: python -m abraxas.alive.core <artifact_json> [tier]")
        print("\nExample:")
        print('  python -m abraxas.alive.core \'{"artifactId": "test", "artifactType": "text", "content": "Hello world"}\' psychonaut')
        sys.exit(1)

    # Parse artifact from command line
    artifact_data = json.loads(sys.argv[1])
    tier = sys.argv[2] if len(sys.argv) > 2 else "psychonaut"

    # Run ALIVE
    result = alive_run(artifact=artifact_data, tier=tier)

    # Output result as JSON
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
