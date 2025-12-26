"""
Test: Scenario Cascade Sheet Artifact

Verifies cascade sheet generation with golden outputs.
"""

import json
from pathlib import Path

import pytest

from abraxas.artifacts.scenario_cascade_sheet import generate_scenario_cascade_sheet
from abraxas.scenario.types import ScenarioEnvelope, ScenarioInput, ScenarioRunResult


@pytest.fixture
def mock_scenario_result():
    """Create mock scenario result for testing."""
    scenario_input = ScenarioInput(
        run_id="test_cascade_001",
        timestamp="2025-01-01T00:00:00+00:00",
        sim_priors={"MRI": 0.6, "IRI": 0.55, "tau_memory": 0.5, "tau_latency": 0.3},
        current_weather=None,
        dm_snapshot=None,
        almanac_snapshot=None,
        notes=None,
    )

    envelopes = [
        ScenarioEnvelope(
            label="baseline",
            priors={"MRI": 0.6, "IRI": 0.55, "tau_memory": 0.5, "tau_latency": 0.3},
            outputs={
                "ncp": {
                    "paths": [
                        {
                            "path_id": "path_001",
                            "trigger": "Viral meme emerges",
                            "probability": 0.75,
                            "duration_hours": 48,
                            "terminus": "Saturation",
                        },
                        {
                            "path_id": "path_002",
                            "trigger": "Influencer amplification",
                            "probability": 0.60,
                            "duration_hours": 72,
                            "terminus": "Containment",
                        },
                    ]
                },
                "cnf": {"counters": []},
                "efte": {"thresholds": []},
            },
            confidence="HIGH",
            falsifiers=["Spread diverges from baseline MRI"],
        )
    ]

    provenance = {
        "generator": "scenario_envelope_runner",
        "version": "1.0.0",
        "timestamp": "2025-01-01T00:00:00+00:00",
        "envelope_count": 1,
    }

    return ScenarioRunResult(
        input=scenario_input, envelopes=envelopes, provenance=provenance
    )


def test_generate_cascade_sheet_json(mock_scenario_result):
    """Test JSON cascade sheet generation."""
    outputs = generate_scenario_cascade_sheet(
        result=mock_scenario_result, format="json"
    )

    assert "json" in outputs
    cascade_json = json.loads(outputs["json"])

    assert cascade_json["run_id"] == "test_cascade_001"
    assert len(cascade_json["envelopes"]) == 1
    assert cascade_json["envelopes"][0]["label"] == "baseline"


def test_generate_cascade_sheet_md(mock_scenario_result):
    """Test Markdown cascade sheet generation."""
    outputs = generate_scenario_cascade_sheet(
        result=mock_scenario_result, format="md"
    )

    assert "md" in outputs
    cascade_md = outputs["md"]

    assert "# Scenario Cascade Sheet" in cascade_md
    assert "test_cascade_001" in cascade_md
    assert "baseline" in cascade_md
    assert "HIGH" in cascade_md


def test_generate_cascade_sheet_both(mock_scenario_result):
    """Test both JSON and Markdown generation."""
    outputs = generate_scenario_cascade_sheet(
        result=mock_scenario_result, format="both"
    )

    assert "json" in outputs
    assert "md" in outputs


def test_generate_cascade_sheet_with_focus_cluster(mock_scenario_result):
    """Test cascade sheet with focus cluster."""
    outputs = generate_scenario_cascade_sheet(
        result=mock_scenario_result, focus_cluster="crypto_discourse", format="both"
    )

    cascade_json = json.loads(outputs["json"])
    assert cascade_json["focus_cluster"] == "crypto_discourse"

    cascade_md = outputs["md"]
    assert "crypto_discourse" in cascade_md


def test_generate_cascade_sheet_golden_json(mock_scenario_result):
    """Test against golden JSON output."""
    outputs = generate_scenario_cascade_sheet(
        result=mock_scenario_result, format="json"
    )

    golden_path = Path("tests/golden/scenario/cascade_sheet.json")
    golden_path.parent.mkdir(parents=True, exist_ok=True)

    # Write golden (uncomment to regenerate)
    # with open(golden_path, "w") as f:
    #     f.write(outputs["json"])

    # Compare to golden
    if golden_path.exists():
        with open(golden_path, "r") as f:
            golden_json = f.read()

        # Both should be valid JSON
        result_data = json.loads(outputs["json"])
        golden_data = json.loads(golden_json)

        # Compare structure
        assert result_data["run_id"] == golden_data["run_id"]
        assert len(result_data["envelopes"]) == len(golden_data["envelopes"])


def test_generate_cascade_sheet_golden_md(mock_scenario_result):
    """Test against golden Markdown output."""
    outputs = generate_scenario_cascade_sheet(
        result=mock_scenario_result, format="md"
    )

    golden_path = Path("tests/golden/scenario/cascade_sheet.md")
    golden_path.parent.mkdir(parents=True, exist_ok=True)

    # Write golden (uncomment to regenerate)
    # with open(golden_path, "w") as f:
    #     f.write(outputs["md"])

    # Compare to golden
    if golden_path.exists():
        with open(golden_path, "r") as f:
            golden_md = f.read()

        # Should contain key elements
        for key_element in ["# Scenario Cascade Sheet", "test_cascade_001", "baseline"]:
            assert key_element in outputs["md"]
            assert key_element in golden_md
