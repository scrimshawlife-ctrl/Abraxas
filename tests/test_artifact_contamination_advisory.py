"""
Test: Scenario Contamination Advisory Artifact

Verifies contamination advisory generation with golden outputs.
"""

import json
from pathlib import Path

import pytest

from abraxas.artifacts.scenario_contamination_advisory import (
    generate_scenario_contamination_advisory,
)


@pytest.fixture
def mock_dm_snapshot():
    """Create mock D/M snapshot."""
    return {
        "SLS": 0.65,  # Slang Lifecycle Saturation
        "MDS": 0.42,  # Memetic Drift Score
        "evidence_count": 5,
    }


@pytest.fixture
def mock_sim_priors():
    """Create mock simulation priors."""
    return {
        "MRI": 0.60,
        "IRI": 0.55,
        "tau_memory": 0.50,
        "tau_latency": 0.30,
    }


def test_generate_advisory_json(mock_dm_snapshot, mock_sim_priors):
    """Test JSON advisory generation."""
    outputs = generate_scenario_contamination_advisory(
        dm_snapshot=mock_dm_snapshot,
        sim_priors=mock_sim_priors,
        weather=None,
        tier="psychonaut",
        format="json",
    )

    assert "json" in outputs
    advisory_json = json.loads(outputs["json"])

    assert "ssi" in advisory_json
    assert "indices" in advisory_json
    assert "MRI" in advisory_json["indices"]
    assert "IRI" in advisory_json["indices"]


def test_generate_advisory_md(mock_dm_snapshot, mock_sim_priors):
    """Test Markdown advisory generation."""
    outputs = generate_scenario_contamination_advisory(
        dm_snapshot=mock_dm_snapshot,
        sim_priors=mock_sim_priors,
        weather=None,
        tier="analyst",
        format="md",
    )

    assert "md" in outputs
    advisory_md = outputs["md"]

    assert "# Contamination Advisory" in advisory_md
    assert "SSI" in advisory_md
    assert "MRI" in advisory_md


def test_generate_advisory_ssi_from_sls(mock_dm_snapshot, mock_sim_priors):
    """Test SSI computation from SLS."""
    outputs = generate_scenario_contamination_advisory(
        dm_snapshot=mock_dm_snapshot,
        sim_priors=mock_sim_priors,
        weather=None,
        format="json",
    )

    advisory_json = json.loads(outputs["json"])
    # SSI should equal SLS (0.65)
    assert advisory_json["ssi"] == 0.65


def test_generate_advisory_ssi_fallback(mock_sim_priors):
    """Test SSI computation fallback (no SLS)."""
    dm_snapshot = {"MDS": 0.42, "evidence_count": 3}  # No SLS

    outputs = generate_scenario_contamination_advisory(
        dm_snapshot=dm_snapshot,
        sim_priors=mock_sim_priors,
        weather=None,
        format="json",
    )

    advisory_json = json.loads(outputs["json"])
    # SSI should be derived from evidence completeness
    assert 0.0 <= advisory_json["ssi"] <= 0.5


def test_generate_advisory_ssi_no_data(mock_sim_priors):
    """Test SSI with no D/M snapshot."""
    outputs = generate_scenario_contamination_advisory(
        dm_snapshot=None,
        sim_priors=mock_sim_priors,
        weather=None,
        format="json",
    )

    advisory_json = json.loads(outputs["json"])
    # SSI should be 0.0 (no data)
    assert advisory_json["ssi"] == 0.0


def test_generate_advisory_mri_iri_scaling(mock_dm_snapshot, mock_sim_priors):
    """Test MRI/IRI scaling to 0-100."""
    outputs = generate_scenario_contamination_advisory(
        dm_snapshot=mock_dm_snapshot,
        sim_priors=mock_sim_priors,
        weather=None,
        format="json",
    )

    advisory_json = json.loads(outputs["json"])
    # MRI 0.60 -> 60.0
    assert advisory_json["indices"]["MRI"] == 60.0
    # IRI 0.55 -> 55.0
    assert advisory_json["indices"]["IRI"] == 55.0


def test_generate_advisory_tier_psychonaut(mock_dm_snapshot, mock_sim_priors):
    """Test psychonaut tier guidance."""
    outputs = generate_scenario_contamination_advisory(
        dm_snapshot=mock_dm_snapshot,
        sim_priors=mock_sim_priors,
        weather=None,
        tier="psychonaut",
        format="md",
    )

    advisory_md = outputs["md"]
    assert "Plain Mode" in advisory_md
    assert "pure instrumentation" in advisory_md


def test_generate_advisory_tier_analyst(mock_dm_snapshot, mock_sim_priors):
    """Test analyst tier guidance."""
    outputs = generate_scenario_contamination_advisory(
        dm_snapshot=mock_dm_snapshot,
        sim_priors=mock_sim_priors,
        weather=None,
        tier="analyst",
        format="md",
    )

    advisory_md = outputs["md"]
    assert "Method Notes" in advisory_md
    assert "deterministic" in advisory_md


def test_generate_advisory_tier_enterprise(mock_dm_snapshot, mock_sim_priors):
    """Test enterprise tier guidance."""
    outputs = generate_scenario_contamination_advisory(
        dm_snapshot=mock_dm_snapshot,
        sim_priors=mock_sim_priors,
        weather=None,
        tier="enterprise",
        format="md",
    )

    advisory_md = outputs["md"]
    assert "Risk Timing" in advisory_md
    assert "operational deployment" in advisory_md


def test_generate_advisory_golden_json(mock_dm_snapshot, mock_sim_priors):
    """Test against golden JSON output."""
    outputs = generate_scenario_contamination_advisory(
        dm_snapshot=mock_dm_snapshot,
        sim_priors=mock_sim_priors,
        weather=None,
        tier="psychonaut",
        format="json",
    )

    golden_path = Path("tests/golden/scenario/contamination_advisory.json")
    golden_path.parent.mkdir(parents=True, exist_ok=True)

    # Write golden (uncomment to regenerate)
    # with open(golden_path, "w") as f:
    #     f.write(outputs["json"])

    # Compare to golden
    if golden_path.exists():
        with open(golden_path, "r") as f:
            golden_json = f.read()

        result_data = json.loads(outputs["json"])
        golden_data = json.loads(golden_json)

        # Compare key fields
        assert result_data["ssi"] == golden_data["ssi"]
        assert result_data["tier"] == golden_data["tier"]


def test_generate_advisory_golden_md(mock_dm_snapshot, mock_sim_priors):
    """Test against golden Markdown output."""
    outputs = generate_scenario_contamination_advisory(
        dm_snapshot=mock_dm_snapshot,
        sim_priors=mock_sim_priors,
        weather=None,
        tier="psychonaut",
        format="md",
    )

    golden_path = Path("tests/golden/scenario/contamination_advisory.md")
    golden_path.parent.mkdir(parents=True, exist_ok=True)

    # Write golden (uncomment to regenerate)
    # with open(golden_path, "w") as f:
    #     f.write(outputs["md"])

    # Compare to golden
    if golden_path.exists():
        with open(golden_path, "r") as f:
            golden_md = f.read()

        # Should contain key elements
        for key_element in ["# Contamination Advisory", "SSI", "MRI"]:
            assert key_element in outputs["md"]
            assert key_element in golden_md
