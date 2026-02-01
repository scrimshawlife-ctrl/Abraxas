"""
ABX-Runes Missing Inputs Test

Validates that runes return not_computable with proper error details
when required input fields are missing or invalid.
"""
from __future__ import annotations

import os
import pytest
from typing import Any, Dict

from abraxas_ase.runes import invoke_rune, RuneNotFoundError, clear_caches


@pytest.fixture(autouse=True)
def set_ase_key():
    """Set deterministic ASE_KEY for all tests."""
    original = os.environ.get("ASE_KEY")
    os.environ["ASE_KEY"] = "test-missing-inputs-key"
    yield
    if original is not None:
        os.environ["ASE_KEY"] = original
    else:
        os.environ.pop("ASE_KEY", None)


@pytest.fixture(autouse=True)
def clear_rune_caches():
    """Clear caches before each test."""
    clear_caches()
    yield
    clear_caches()


class TestMissingItems:
    """Test handling of missing/invalid items field."""

    def test_missing_items_field(self):
        """
        Payload without 'items' key returns not_computable.
        """
        rune_id = "sdct.text_subword.v1"
        payload: Dict[str, Any] = {"params": {}}  # No items
        ctx = {"run_id": "TEST-MISSING", "date": "2026-01-24"}

        result = invoke_rune(rune_id, payload, ctx)

        assert result["not_computable"] is not None
        assert result["not_computable"]["field"] == "items"
        assert "required" in result["not_computable"]["reason"].lower()
        assert result["evidence_rows"] == []
        assert result["motif_stats"] == []

    def test_empty_items_list(self):
        """
        Empty items list returns not_computable.
        """
        rune_id = "sdct.text_subword.v1"
        payload = {"items": []}
        ctx = {"run_id": "TEST-EMPTY", "date": "2026-01-24"}

        result = invoke_rune(rune_id, payload, ctx)

        assert result["not_computable"] is not None
        assert result["not_computable"]["field"] == "items"
        assert "empty" in result["not_computable"]["reason"].lower()

    def test_items_none(self):
        """
        items=None returns not_computable.
        """
        rune_id = "sdct.text_subword.v1"
        payload = {"items": None}
        ctx = {"run_id": "TEST-NONE", "date": "2026-01-24"}

        result = invoke_rune(rune_id, payload, ctx)

        assert result["not_computable"] is not None
        assert result["not_computable"]["field"] == "items"


class TestMalformedItems:
    """Test handling of malformed item objects."""

    def test_item_not_dict(self):
        """
        Items containing non-dict elements return not_computable.
        """
        rune_id = "sdct.text_subword.v1"
        payload = {"items": ["not a dict", 123, None]}
        ctx = {"run_id": "TEST-BAD-TYPE", "date": "2026-01-24"}

        result = invoke_rune(rune_id, payload, ctx)

        assert result["not_computable"] is not None
        assert "not a dict" in result["not_computable"]["reason"].lower()

    def test_item_missing_id(self):
        """
        Item missing 'id' field returns not_computable.
        """
        rune_id = "sdct.text_subword.v1"
        payload = {
            "items": [{
                # Missing id
                "source": "test",
                "published_at": "2026-01-24T00:00:00Z",
                "title": "Test",
                "text": "Test text",
            }]
        }
        ctx = {"run_id": "TEST-NO-ID", "date": "2026-01-24"}

        result = invoke_rune(rune_id, payload, ctx)

        assert result["not_computable"] is not None
        assert "missing" in result["not_computable"]["reason"].lower()
        assert "id" in result["not_computable"]["reason"].lower()

    def test_item_missing_source(self):
        """
        Item missing 'source' field returns not_computable.
        """
        rune_id = "sdct.text_subword.v1"
        payload = {
            "items": [{
                "id": "test-1",
                # Missing source
                "published_at": "2026-01-24T00:00:00Z",
                "title": "Test",
                "text": "Test text",
            }]
        }
        ctx = {"run_id": "TEST-NO-SOURCE", "date": "2026-01-24"}

        result = invoke_rune(rune_id, payload, ctx)

        assert result["not_computable"] is not None
        assert "source" in result["not_computable"]["reason"].lower()

    def test_item_missing_title(self):
        """
        Item missing 'title' field returns not_computable.
        """
        rune_id = "sdct.text_subword.v1"
        payload = {
            "items": [{
                "id": "test-1",
                "source": "test",
                "published_at": "2026-01-24T00:00:00Z",
                # Missing title
                "text": "Test text",
            }]
        }
        ctx = {"run_id": "TEST-NO-TITLE", "date": "2026-01-24"}

        result = invoke_rune(rune_id, payload, ctx)

        assert result["not_computable"] is not None
        assert "title" in result["not_computable"]["reason"].lower()

    def test_item_missing_text(self):
        """
        Item missing 'text' field returns not_computable.
        """
        rune_id = "sdct.text_subword.v1"
        payload = {
            "items": [{
                "id": "test-1",
                "source": "test",
                "published_at": "2026-01-24T00:00:00Z",
                "title": "Test Title",
                # Missing text
            }]
        }
        ctx = {"run_id": "TEST-NO-TEXT", "date": "2026-01-24"}

        result = invoke_rune(rune_id, payload, ctx)

        assert result["not_computable"] is not None
        assert "text" in result["not_computable"]["reason"].lower()

    def test_item_missing_published_at(self):
        """
        Item missing 'published_at' field returns not_computable.
        """
        rune_id = "sdct.text_subword.v1"
        payload = {
            "items": [{
                "id": "test-1",
                "source": "test",
                # Missing published_at
                "title": "Test Title",
                "text": "Test text",
            }]
        }
        ctx = {"run_id": "TEST-NO-PUBDATE", "date": "2026-01-24"}

        result = invoke_rune(rune_id, payload, ctx)

        assert result["not_computable"] is not None
        assert "published_at" in result["not_computable"]["reason"].lower()

    def test_multiple_missing_fields(self):
        """
        Item missing multiple fields reports at least one.
        """
        rune_id = "sdct.text_subword.v1"
        payload = {
            "items": [{
                "id": "test-1",
                # Missing: source, published_at, title, text
            }]
        }
        ctx = {"run_id": "TEST-MULTI-MISSING", "date": "2026-01-24"}

        result = invoke_rune(rune_id, payload, ctx)

        assert result["not_computable"] is not None
        assert "missing" in result["not_computable"]["reason"].lower()


class TestUnknownRune:
    """Test handling of unknown rune IDs."""

    def test_unknown_rune_raises_error(self):
        """
        Invoking unknown rune_id raises RuneNotFoundError.
        """
        with pytest.raises(RuneNotFoundError) as exc_info:
            invoke_rune("sdct.nonexistent.v99", {"items": []}, {})

        assert "sdct.nonexistent.v99" in str(exc_info.value)

    def test_empty_rune_id_raises_error(self):
        """
        Empty rune_id raises RuneNotFoundError.
        """
        with pytest.raises(RuneNotFoundError):
            invoke_rune("", {"items": []}, {})


class TestProvenanceOnNotComputable:
    """Test that provenance is still provided on not_computable results."""

    def test_provenance_present_on_error(self):
        """
        Provenance envelope is present even when not_computable.
        """
        rune_id = "sdct.text_subword.v1"
        payload: Dict[str, Any] = {}  # Missing items
        ctx = {"run_id": "TEST-PROV-ERROR", "date": "2026-01-24"}

        result = invoke_rune(rune_id, payload, ctx)

        assert "provenance" in result
        assert result["provenance"]["rune_id"] == rune_id

    def test_input_hash_present_on_error(self):
        """
        Input hash is computed even when not_computable.
        """
        rune_id = "sdct.text_subword.v1"
        payload: Dict[str, Any] = {"items": None}
        ctx = {"run_id": "TEST-HASH-ERROR", "date": "2026-01-24"}

        result = invoke_rune(rune_id, payload, ctx)

        # Input hash should be in provenance from invoke layer
        assert "input_hash" in result["provenance"]


class TestValidPayloadSucceeds:
    """Sanity check that valid payloads succeed."""

    def test_valid_single_item_succeeds(self):
        """
        Valid single item payload returns evidence (not not_computable).
        """
        rune_id = "sdct.text_subword.v1"
        payload = {
            "items": [{
                "id": "valid-1",
                "source": "test",
                "published_at": "2026-01-24T00:00:00Z",
                "title": "TRADE WAR ESCALATES",
                "text": "Economic tensions rise as war of words continues.",
            }]
        }
        ctx = {"run_id": "TEST-VALID", "date": "2026-01-24"}

        result = invoke_rune(rune_id, payload, ctx)

        assert result["not_computable"] is None
        assert len(result["evidence_rows"]) > 0


# Import for cleanup
from abraxas_ase.runes.invoke import clear_caches
