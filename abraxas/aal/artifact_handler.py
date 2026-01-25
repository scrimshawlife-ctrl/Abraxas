"""Artifact storage handler for Neon-Genie outputs.

Stores Neon-Genie symbolic generation results as deterministic artifacts
with SHA-256 provenance tracking.

DUAL-LANE PRINCIPLE:
- All Neon-Genie outputs stored as artifacts only
- Never fed into forecast weights or prediction lanes
- Tagged with no_influence=True for governance compliance
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from abraxas.runtime.artifacts import ArtifactWriter


class NeonGenieArtifactHandler:
    """
    Handles deterministic storage of Neon-Genie outputs.

    All outputs are:
    - Written to disk with SHA-256 tracking
    - Stored in artifact registry manifest
    - Tagged with no_influence=True
    - Never used in forecast scoring
    """

    def __init__(self, artifacts_dir: Optional[Path] = None):
        """
        Initialize artifact handler.

        Args:
            artifacts_dir: Base directory for artifacts (default: out/artifacts/)
        """
        self.artifacts_dir = artifacts_dir or Path("out/artifacts")
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.writer = ArtifactWriter(artifacts_dir=str(self.artifacts_dir))

    def store_generation_result(
        self,
        *,
        run_id: str,
        tick: int,
        prompt: str,
        generated_output: Any,
        provenance: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Store Neon-Genie generation result as artifact.

        Args:
            run_id: Unique run identifier
            tick: Tick number for ordering
            prompt: Original generation prompt
            generated_output: Generated symbolic output
            provenance: Provenance metadata with SHA-256 hashes
            metadata: Additional metadata (must include no_influence=True)

        Returns:
            Artifact record with path, SHA-256, and metadata
        """
        # Validate no_influence flag
        if not metadata.get("no_influence"):
            raise ValueError(
                "Neon-Genie outputs MUST have no_influence=True. "
                "Dual-lane principle violation detected."
            )

        # Construct artifact object
        artifact_obj = {
            "schema": "NeonGenieGeneration.v0",
            "prompt": prompt,
            "generated_output": generated_output,
            "provenance": provenance,
            "metadata": metadata,
        }

        # Generate relative path
        safe_run_id = run_id.replace("/", "_")
        rel_path = f"neon_genie/{safe_run_id}/generation_{tick:04d}.json"

        # Write artifact
        record = self.writer.write_json(
            run_id=run_id,
            tick=tick,
            kind="neon_genie_generation",
            schema="NeonGenieGeneration.v0",
            obj=artifact_obj,
            rel_path=rel_path,
            extra={"no_influence": True, "lane": metadata.get("lane", "OBSERVATION")}
        )

        return {
            "artifact_path": record.path,
            "sha256": record.sha256,
            "bytes": record.bytes,
            "stored_at": record.tick,
            "no_influence": True,
        }

    def retrieve_generation(
        self,
        artifact_path: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve stored generation artifact.

        Args:
            artifact_path: Path to artifact JSON file

        Returns:
            Artifact object or None if not found
        """
        path = Path(artifact_path)
        if not path.exists():
            return None

        with path.open("r") as f:
            return json.load(f)

    def list_generations(
        self,
        run_id: str
    ) -> list[Dict[str, Any]]:
        """
        List all generation artifacts for a run.

        Args:
            run_id: Run identifier

        Returns:
            List of artifact records with metadata
        """
        manifest_path = self.artifacts_dir / "manifests" / f"{run_id}.manifest.json"
        if not manifest_path.exists():
            return []

        with manifest_path.open("r") as f:
            manifest = json.load(f)

        # Filter for Neon-Genie generations only
        generations = [
            record for record in manifest.get("records", [])
            if record.get("kind") == "neon_genie_generation"
        ]

        return generations


def store_neon_genie_result(
    run_id: str,
    tick: int,
    generation_result: Dict[str, Any],
    prompt: str,
) -> Dict[str, Any]:
    """
    Convenience function to store Neon-Genie result.

    Args:
        run_id: Unique run identifier
        tick: Tick number for ordering
        generation_result: Full result from generate_symbolic_v0
        prompt: Original prompt

    Returns:
        Artifact record with storage details
    """
    handler = NeonGenieArtifactHandler()

    return handler.store_generation_result(
        run_id=run_id,
        tick=tick,
        prompt=prompt,
        generated_output=generation_result.get("generated_output"),
        provenance=generation_result.get("provenance"),
        metadata=generation_result.get("metadata", {}),
    )


__all__ = ["NeonGenieArtifactHandler", "store_neon_genie_result"]
