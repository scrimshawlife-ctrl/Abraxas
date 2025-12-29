"""Tests for SML CSV mapping table importer."""

import tempfile
from pathlib import Path

import pytest

from abraxas.sim_mappings.importers import (
    import_mapping_from_csv_row,
    import_mappings_from_csv,
    parse_param_list,
)
from abraxas.sim_mappings.types import ModelFamily


def test_parse_param_list_simple():
    """Test parsing simple semicolon-delimited parameter list."""
    result = parse_param_list("beta; gamma; c2")
    assert result == ["beta", "gamma", "c2"]


def test_parse_param_list_with_whitespace():
    """Test parsing with extra whitespace."""
    result = parse_param_list("  beta  ;  gamma  ;  c2  ")
    assert result == ["beta", "gamma", "c2"]


def test_parse_param_list_single_param():
    """Test parsing single parameter."""
    result = parse_param_list("beta")
    assert result == ["beta"]


def test_parse_param_list_empty():
    """Test parsing empty string."""
    result = parse_param_list("")
    assert result == []


def test_parse_param_list_whitespace_only():
    """Test parsing whitespace-only string."""
    result = parse_param_list("   ")
    assert result == []


def test_parse_param_list_trailing_semicolon():
    """Test parsing with trailing semicolon."""
    result = parse_param_list("beta; gamma; ")
    assert result == ["beta", "gamma"]


def test_import_mapping_from_csv_row_basic():
    """Test importing basic CSV row."""
    row = {
        "paper_id": "PMC12281847",
        "model_family": "DIFFUSION_SIR",
        "mri_params": "beta; c2",
        "iri_params": "gamma",
        "tau_params": "delay",
        "notes": "SIR with media impact"
    }

    result = import_mapping_from_csv_row(row)

    assert result.paper.paper_id == "PMC12281847"
    assert result.family == ModelFamily.DIFFUSION_SIR
    assert len(result.input_params) == 4  # beta, c2, gamma, delay
    assert result.mapped.confidence == "LOW"
    assert result.mapped.mri == 0.0
    assert result.mapped.iri == 0.0
    assert result.notes == "SIR with media impact"


def test_import_mapping_from_csv_row_multiple_mri_params():
    """Test importing row with multiple MRI parameters."""
    row = {
        "paper_id": "TEST001",
        "model_family": "OPINION_DYNAMICS",
        "mri_params": "w_ij; homophily; mu",
        "iri_params": "epsilon",
        "tau_params": "alpha; memory_depth",
        "notes": "Test"
    }

    result = import_mapping_from_csv_row(row)

    assert len(result.input_params) == 6  # 3 MRI + 1 IRI + 2 tau
    param_names = [p.name for p in result.input_params]
    assert "w_ij" in param_names
    assert "homophily" in param_names
    assert "mu" in param_names
    assert "epsilon" in param_names
    assert "alpha" in param_names
    assert "memory_depth" in param_names


def test_import_mapping_from_csv_row_empty_params():
    """Test importing row with empty parameter lists (survey paper)."""
    row = {
        "paper_id": "SURVEY001",
        "model_family": "OPINION_DYNAMICS",
        "mri_params": "",
        "iri_params": "",
        "tau_params": "",
        "notes": "Survey paper, no single parameter set"
    }

    result = import_mapping_from_csv_row(row)

    assert len(result.input_params) == 0
    assert result.mapped.confidence == "LOW"


def test_import_mapping_from_csv_row_missing_paper_id():
    """Test that missing paper_id raises ValueError."""
    row = {
        "model_family": "DIFFUSION_SIR",
        "mri_params": "beta",
        "iri_params": "gamma",
        "tau_params": "",
        "notes": ""
    }

    with pytest.raises(ValueError, match="Missing required field: paper_id"):
        import_mapping_from_csv_row(row)


def test_import_mapping_from_csv_row_missing_model_family():
    """Test that missing model_family raises ValueError."""
    row = {
        "paper_id": "TEST001",
        "mri_params": "beta",
        "iri_params": "gamma",
        "tau_params": "",
        "notes": ""
    }

    with pytest.raises(ValueError, match="Missing required field: model_family"):
        import_mapping_from_csv_row(row)


def test_import_mapping_from_csv_row_invalid_model_family():
    """Test that invalid model_family raises ValueError."""
    row = {
        "paper_id": "TEST001",
        "model_family": "INVALID_FAMILY",
        "mri_params": "beta",
        "iri_params": "gamma",
        "tau_params": "",
        "notes": ""
    }

    with pytest.raises(ValueError, match="Invalid model_family"):
        import_mapping_from_csv_row(row)


def test_import_mapping_from_csv_row_explanation():
    """Test that explanation includes parameter names."""
    row = {
        "paper_id": "TEST001",
        "model_family": "DIFFUSION_SIR",
        "mri_params": "beta; k",
        "iri_params": "gamma",
        "tau_params": "delay",
        "notes": "Test"
    }

    result = import_mapping_from_csv_row(row)

    explanation = result.mapped.explanation
    assert "TEST001" in explanation
    assert "beta, k" in explanation
    assert "gamma" in explanation
    assert "delay" in explanation


def test_import_mappings_from_csv():
    """Test importing full CSV file."""
    csv_content = """paper_id,model_family,mri_params,iri_params,tau_params,notes
PMC12281847,DIFFUSION_SIR,beta; c2,gamma,delay,SIR with media impact
TEST001,OPINION_DYNAMICS,w_ij; homophily,epsilon,alpha,Opinion dynamics test
TEST002,ABM_MISINFO,share_prob; bot_density,correction_eff,content_lifespan,ABM test
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        results = import_mappings_from_csv(temp_path)

        assert len(results) == 3
        assert results[0].paper.paper_id == "PMC12281847"
        assert results[0].family == ModelFamily.DIFFUSION_SIR
        assert results[1].paper.paper_id == "TEST001"
        assert results[1].family == ModelFamily.OPINION_DYNAMICS
        assert results[2].paper.paper_id == "TEST002"
        assert results[2].family == ModelFamily.ABM_MISINFO

    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_import_mappings_from_csv_missing_file():
    """Test that missing CSV file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        import_mappings_from_csv("/nonexistent/path.csv")


def test_import_mappings_from_csv_missing_columns():
    """Test that CSV with missing columns raises ValueError."""
    csv_content = """paper_id,model_family,notes
PMC12281847,DIFFUSION_SIR,Missing param columns
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="CSV missing required columns"):
            import_mappings_from_csv(temp_path)

    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_import_mappings_from_csv_no_header():
    """Test that CSV with no header raises ValueError."""
    csv_content = ""  # Empty file

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="CSV file has no header row"):
            import_mappings_from_csv(temp_path)

    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_import_mapping_param_descriptions():
    """Test that imported parameters have descriptive descriptions."""
    row = {
        "paper_id": "TEST001",
        "model_family": "DIFFUSION_SIR",
        "mri_params": "beta",
        "iri_params": "gamma",
        "tau_params": "delay",
        "notes": "Test"
    }

    result = import_mapping_from_csv_row(row)

    # Check descriptions
    beta_param = next(p for p in result.input_params if p.name == "beta")
    gamma_param = next(p for p in result.input_params if p.name == "gamma")
    delay_param = next(p for p in result.input_params if p.name == "delay")

    assert "MRI" in beta_param.description
    assert "IRI" in gamma_param.description
    assert "Tau" in delay_param.description


def test_import_mapping_null_values():
    """Test that imported parameters have null values."""
    row = {
        "paper_id": "TEST001",
        "model_family": "DIFFUSION_SIR",
        "mri_params": "beta",
        "iri_params": "gamma",
        "tau_params": "",
        "notes": ""
    }

    result = import_mapping_from_csv_row(row)

    # All parameters should have None value (no numeric guessing)
    for param in result.input_params:
        assert param.value is None
