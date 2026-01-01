"""Tests for SML paper registry functions."""

import json
import tempfile
from pathlib import Path

import pytest

from abraxas.sim_mappings.registry import (
    find_by_keyword,
    get_paper_ref,
    list_papers,
    load_paper_refs,
    save_paper_refs,
)
from abraxas.sim_mappings.types import PaperRef


@pytest.fixture
def temp_registry():
    """Create temporary registry file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        registry_data = {
            "papers": [
                {
                    "paper_id": "TEST001",
                    "title": "SIR Model for Test Purposes",
                    "url": "https://example.com/test001",
                    "year": 2024,
                    "notes": "Test paper with SIR model"
                },
                {
                    "paper_id": "TEST002",
                    "title": "Opinion Dynamics Study",
                    "url": "https://example.com/test002",
                    "year": 2023,
                    "notes": "Test paper about opinion formation"
                },
                {
                    "paper_id": "TEST003",
                    "title": "ABM Misinformation Simulation",
                    "url": "https://example.com/test003",
                    "year": None,
                    "notes": "Agent-based model for misinformation"
                },
            ],
            "count": 3,
            "metadata": {
                "last_updated": "2025-12-26",
                "notes": "Test registry"
            }
        }
        json.dump(registry_data, f, indent=2)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


def test_load_paper_refs(temp_registry):
    """Test loading paper references from registry."""
    papers = load_paper_refs(temp_registry)

    assert len(papers) == 3
    assert all(isinstance(p, PaperRef) for p in papers)
    assert papers[0].paper_id == "TEST001"
    assert papers[0].title == "SIR Model for Test Purposes"
    assert papers[0].year == 2024


def test_load_paper_refs_nonexistent():
    """Test loading from non-existent file returns empty list."""
    papers = load_paper_refs("/nonexistent/path.json")
    assert papers == []


def test_get_paper_ref(temp_registry):
    """Test retrieving specific paper by ID."""
    paper = get_paper_ref("TEST002", temp_registry)

    assert paper is not None
    assert paper.paper_id == "TEST002"
    assert paper.title == "Opinion Dynamics Study"
    assert paper.year == 2023


def test_get_paper_ref_not_found(temp_registry):
    """Test retrieving non-existent paper returns None."""
    paper = get_paper_ref("NONEXISTENT", temp_registry)
    assert paper is None


def test_save_paper_refs():
    """Test saving paper references to registry."""
    papers = [
        PaperRef(
            paper_id="SAVE001",
            title="Test Save Paper",
            url="https://example.com/save001",
            year=2025,
            notes="Test save"
        ),
        PaperRef(
            paper_id="SAVE002",
            title="Another Test Paper",
            url="https://example.com/save002",
            year=None,
        ),
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "test_registry.json"

        save_paper_refs(papers, str(registry_path))

        # Verify file was created
        assert registry_path.exists()

        # Load and verify content
        with open(registry_path, "r") as f:
            data = json.load(f)

        assert data["count"] == 2
        assert len(data["papers"]) == 2
        assert data["papers"][0]["paper_id"] == "SAVE001"
        assert data["papers"][1]["year"] is None


def test_list_papers(temp_registry):
    """Test listing papers with summary info."""
    papers = list_papers(temp_registry)

    assert len(papers) == 3
    assert all(isinstance(p, dict) for p in papers)

    # Check first paper
    assert papers[0]["paper_id"] == "TEST001"
    assert papers[0]["title"] == "SIR Model for Test Purposes"
    assert papers[0]["year"] == "2024"
    assert papers[0]["notes"] == "Test paper with SIR model"

    # Check paper with no year
    assert papers[2]["paper_id"] == "TEST003"
    assert papers[2]["year"] == "N/A"


def test_find_by_keyword_in_title(temp_registry):
    """Test finding papers by keyword in title."""
    results = find_by_keyword("Opinion", temp_registry)

    assert len(results) == 1
    assert results[0].paper_id == "TEST002"


def test_find_by_keyword_in_notes(temp_registry):
    """Test finding papers by keyword in notes."""
    results = find_by_keyword("SIR model", temp_registry)

    assert len(results) == 1
    assert results[0].paper_id == "TEST001"


def test_find_by_keyword_in_paper_id(temp_registry):
    """Test finding papers by keyword in paper_id."""
    results = find_by_keyword("TEST003", temp_registry)

    assert len(results) == 1
    assert results[0].paper_id == "TEST003"


def test_find_by_keyword_case_insensitive(temp_registry):
    """Test case-insensitive keyword search."""
    # Search with lowercase, should match uppercase in title
    results = find_by_keyword("abm", temp_registry, case_sensitive=False)

    assert len(results) == 1
    assert results[0].paper_id == "TEST003"


def test_find_by_keyword_case_sensitive(temp_registry):
    """Test case-sensitive keyword search."""
    # Search with lowercase, should NOT match uppercase
    results = find_by_keyword("abm", temp_registry, case_sensitive=True)
    assert len(results) == 0

    # Search with correct case
    results = find_by_keyword("ABM", temp_registry, case_sensitive=True)
    assert len(results) == 1


def test_find_by_keyword_multiple_matches(temp_registry):
    """Test finding multiple papers with same keyword."""
    results = find_by_keyword("test", temp_registry, case_sensitive=False)

    # All papers should match (either in title or notes)
    assert len(results) >= 2


def test_find_by_keyword_no_matches(temp_registry):
    """Test keyword search with no matches."""
    results = find_by_keyword("NONEXISTENT_KEYWORD", temp_registry)
    assert len(results) == 0


def test_roundtrip_save_load():
    """Test save and load roundtrip preserves data."""
    original_papers = [
        PaperRef(
            paper_id="RT001",
            title="Roundtrip Test",
            url="https://example.com/rt001",
            year=2025,
            notes="Test roundtrip"
        ),
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "roundtrip.json"

        # Save
        save_paper_refs(original_papers, str(registry_path))

        # Load
        loaded_papers = load_paper_refs(str(registry_path))

        # Verify
        assert len(loaded_papers) == 1
        assert loaded_papers[0].paper_id == original_papers[0].paper_id
        assert loaded_papers[0].title == original_papers[0].title
        assert loaded_papers[0].url == original_papers[0].url
        assert loaded_papers[0].year == original_papers[0].year
        assert loaded_papers[0].notes == original_papers[0].notes
