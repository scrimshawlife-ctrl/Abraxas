"""Tests for Neon-Genie ABX-Runes adapter.

Tests verify:
- Rune invocation contract compliance
- Deterministic provenance tracking
- No-influence flag enforcement (DUAL-LANE PRINCIPLE)
- Artifact storage and retrieval
- Schema validation for inputs/outputs
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from abraxas.aal.neon_genie_adapter import generate_symbolic_v0
from abraxas.aal.artifact_handler import (
    NeonGenieArtifactHandler,
    store_neon_genie_result,
)
from abraxas.core.provenance import hash_canonical_json


def test_generate_symbolic_v0_missing_prompt() -> None:
    """Test that missing prompt returns not_computable."""
    result = generate_symbolic_v0(
        prompt="",
        seed=42
    )

    assert result["generated_output"] is None
    assert result["not_computable"] is not None
    assert "Invalid or missing prompt" in result["not_computable"]["reason"]
    assert result["metadata"]["no_influence"] is True
    assert result["metadata"]["lane"] == "OBSERVATION"


def test_generate_symbolic_v0_overlay_not_available() -> None:
    """Test graceful failure when overlay runtime not available."""
    # Mock the internal stub to return None (overlay not available)
    with patch("abraxas.aal.neon_genie_adapter._invoke_neon_genie_overlay", return_value=None):
        result = generate_symbolic_v0(
            prompt="Generate a symbolic representation of truth",
            seed=42
        )

    assert result["generated_output"] is None
    assert result["not_computable"] is not None
    assert "stub mode" in result["not_computable"]["reason"].lower()
    assert result["metadata"]["no_influence"] is True


def test_generate_symbolic_v0_overlay_invocation_error() -> None:
    """Test graceful failure when overlay invocation raises exception."""
    # Mock the internal stub to raise an exception
    with patch("abraxas.aal.neon_genie_adapter._invoke_neon_genie_overlay", side_effect=RuntimeError("Overlay error")):
        result = generate_symbolic_v0(
            prompt="Generate a symbolic representation of truth",
            seed=42
        )

    assert result["generated_output"] is None
    assert result["not_computable"] is not None
    assert "Neon-Genie invocation failed" in result["not_computable"]["reason"]
    assert result["metadata"]["no_influence"] is True


def test_generate_symbolic_v0_successful_generation() -> None:
    """Test successful generation with mocked overlay."""
    mock_generated_output = {
        "text": "A symbolic glyph representing cascading truth",
        "confidence": 0.85,
        "tokens_used": 42
    }

    with patch("abraxas.aal.neon_genie_adapter._invoke_neon_genie_overlay", return_value=mock_generated_output):
        result = generate_symbolic_v0(
            prompt="Generate a symbolic representation of truth",
            context={"term": "truth", "motif": "cascade"},
            seed=42
        )

    # Verify successful result
    assert result["generated_output"] is not None
    assert result["generated_output"]["text"] == "A symbolic glyph representing cascading truth"
    assert result["provenance"] is not None
    assert result["not_computable"] is None

    # CRITICAL: Verify no-influence flag
    assert result["metadata"]["no_influence"] is True
    assert result["metadata"]["lane"] == "OBSERVATION"
    assert result["metadata"]["artifact_only"] is True


def test_generate_symbolic_v0_golden_provenance() -> None:
    """Test deterministic provenance hashes for a fixed generation."""
    mock_generated_output = {
        "text": "A luminous glyph of convergence",
        "confidence": 0.91,
        "tokens_used": 64
    }
    prompt = "Generate a symbolic representation of convergence"
    context = {"term": "convergence", "motif": "lattice", "mode": "symbolic"}
    config = {"max_length": 512}

    with patch("abraxas.aal.neon_genie_adapter._invoke_neon_genie_overlay", return_value=mock_generated_output):
        result = generate_symbolic_v0(
            prompt=prompt,
            context=context,
            config=config,
            seed=17
        )

    assert result["generated_output"] == mock_generated_output
    assert result["provenance"] is not None
    assert result["provenance"]["config_sha256"] == hash_canonical_json(config)
    assert result["provenance"]["inputs_sha256"] == hash_canonical_json(
        {"prompt": prompt, "context": context}
    )


def test_generate_symbolic_v0_deterministic_hashes() -> None:
    """Test that same inputs produce same provenance hashes."""
    mock_generated_output = {"text": "Deterministic output"}

    with patch("abraxas.aal.neon_genie_adapter._invoke_neon_genie_overlay", return_value=mock_generated_output):
        result1 = generate_symbolic_v0(
            prompt="Test prompt",
            context={"term": "test"},
            seed=42
        )

        result2 = generate_symbolic_v0(
            prompt="Test prompt",
            context={"term": "test"},
            seed=42
        )

    # Verify deterministic provenance hashes (inputs should match)
    # Note: timestamp will differ, but inputs_sha256 should match
    assert result1["provenance"]["inputs_sha256"] == result2["provenance"]["inputs_sha256"]
    assert result1["provenance"]["config_sha256"] == result2["provenance"]["config_sha256"]


def test_generate_symbolic_v0_with_context_modes() -> None:
    """Test generation with different context modes."""
    mock_generated_output = {"text": "Narrative output"}

    with patch("abraxas.aal.neon_genie_adapter._invoke_neon_genie_overlay", return_value=mock_generated_output):
        result = generate_symbolic_v0(
            prompt="Test prompt",
            context={"mode": "narrative"},
            seed=42
        )

    assert result["generated_output"] is not None
    assert result["metadata"]["generation_mode"] == "narrative"
    assert result["metadata"]["no_influence"] is True


def test_artifact_handler_store_generation(tmp_path: Path) -> None:
    """Test artifact storage with NeonGenieArtifactHandler."""
    handler = NeonGenieArtifactHandler(artifacts_dir=tmp_path)

    mock_provenance = {
        "timestamp_utc": "2026-01-18T00:00:00Z",
        "config_sha256": "a" * 64,
        "inputs_sha256": "b" * 64,
        "operation_id": "aal.neon_genie.generate.v0"
    }

    mock_metadata = {
        "no_influence": True,
        "lane": "OBSERVATION",
        "artifact_only": True
    }

    record = handler.store_generation_result(
        run_id="TEST-RUN-001",
        tick=1,
        prompt="Test prompt",
        generated_output={"text": "Test output"},
        provenance=mock_provenance,
        metadata=mock_metadata
    )

    # Verify artifact record
    assert record["no_influence"] is True
    assert "neon_genie" in record["artifact_path"]
    assert len(record["sha256"]) == 64
    assert record["bytes"] > 0

    # Verify artifact file exists
    artifact_path = Path(record["artifact_path"])
    assert artifact_path.exists()

    # Verify artifact content
    with artifact_path.open("r") as f:
        artifact_obj = json.load(f)
        assert artifact_obj["schema"] == "NeonGenieGeneration.v0"
        assert artifact_obj["prompt"] == "Test prompt"
        assert artifact_obj["generated_output"]["text"] == "Test output"
        assert artifact_obj["metadata"]["no_influence"] is True


def test_artifact_handler_no_influence_validation(tmp_path: Path) -> None:
    """Test that artifact handler enforces no_influence=True."""
    handler = NeonGenieArtifactHandler(artifacts_dir=tmp_path)

    mock_provenance = {
        "timestamp_utc": "2026-01-18T00:00:00Z",
        "config_sha256": "a" * 64,
        "inputs_sha256": "b" * 64
    }

    # Attempt to store with no_influence=False (VIOLATION)
    with pytest.raises(ValueError, match="no_influence=True"):
        handler.store_generation_result(
            run_id="TEST-RUN-001",
            tick=1,
            prompt="Test prompt",
            generated_output={"text": "Test output"},
            provenance=mock_provenance,
            metadata={"no_influence": False}  # VIOLATION
        )


def test_artifact_handler_retrieve_generation(tmp_path: Path) -> None:
    """Test artifact retrieval."""
    handler = NeonGenieArtifactHandler(artifacts_dir=tmp_path)

    mock_provenance = {
        "timestamp_utc": "2026-01-18T00:00:00Z",
        "config_sha256": "a" * 64,
        "inputs_sha256": "b" * 64
    }

    mock_metadata = {
        "no_influence": True,
        "lane": "OBSERVATION"
    }

    # Store artifact
    record = handler.store_generation_result(
        run_id="TEST-RUN-001",
        tick=1,
        prompt="Test prompt",
        generated_output={"text": "Test output"},
        provenance=mock_provenance,
        metadata=mock_metadata
    )

    # Retrieve artifact
    retrieved = handler.retrieve_generation(record["artifact_path"])
    assert retrieved is not None
    assert retrieved["prompt"] == "Test prompt"
    assert retrieved["metadata"]["no_influence"] is True


def test_artifact_handler_list_generations(tmp_path: Path) -> None:
    """Test listing all generations for a run."""
    handler = NeonGenieArtifactHandler(artifacts_dir=tmp_path)

    mock_provenance = {
        "timestamp_utc": "2026-01-18T00:00:00Z",
        "config_sha256": "a" * 64,
        "inputs_sha256": "b" * 64
    }

    mock_metadata = {
        "no_influence": True,
        "lane": "OBSERVATION"
    }

    # Store multiple generations
    for i in range(3):
        handler.store_generation_result(
            run_id="TEST-RUN-001",
            tick=i + 1,
            prompt=f"Prompt {i}",
            generated_output={"text": f"Output {i}"},
            provenance=mock_provenance,
            metadata=mock_metadata
        )

    # List generations
    generations = handler.list_generations("TEST-RUN-001")
    assert len(generations) == 3
    assert all(g["kind"] == "neon_genie_generation" for g in generations)


def test_store_neon_genie_result_convenience_function(tmp_path: Path) -> None:
    """Test convenience function for storing results."""
    # Mock the handler to use tmp_path
    with patch("abraxas.aal.artifact_handler.NeonGenieArtifactHandler") as mock_handler_class:
        mock_handler = MagicMock()
        mock_handler.store_generation_result.return_value = {
            "artifact_path": "/path/to/artifact.json",
            "sha256": "a" * 64,
            "bytes": 1024,
            "stored_at": 1,
            "no_influence": True
        }
        mock_handler_class.return_value = mock_handler

        generation_result = {
            "generated_output": {"text": "Test output"},
            "provenance": {
                "timestamp_utc": "2026-01-18T00:00:00Z",
                "config_sha256": "a" * 64,
                "inputs_sha256": "b" * 64
            },
            "metadata": {
                "no_influence": True,
                "lane": "OBSERVATION"
            }
        }

        record = store_neon_genie_result(
            run_id="TEST-RUN-001",
            tick=1,
            generation_result=generation_result,
            prompt="Test prompt"
        )

        assert record["no_influence"] is True
        mock_handler.store_generation_result.assert_called_once()
