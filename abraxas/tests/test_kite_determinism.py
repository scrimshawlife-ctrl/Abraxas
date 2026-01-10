import os
from pathlib import Path

from abraxas.admin.kite.storage import canonicalize_text, insert_item, list_items, normalize_tags, sha256_hex


def test_kite_deterministic_ingest(tmp_path, monkeypatch):
    monkeypatch.setenv("KITE_ROOT", str(tmp_path / "kite"))
    monkeypatch.setenv("KITE_NOW", "1970-01-01T00:00:00Z")

    tags = normalize_tags(["Test", "test ", "ALPHA"])
    text = canonicalize_text("Hello\nWorld")
    content_sha = sha256_hex(text)
    item_id = insert_item(
        title="Sample",
        source_type="text",
        tags=tags,
        content_sha=content_sha,
        file_path=None,
        text_content=text,
    )
    item_id_again = insert_item(
        title="Sample",
        source_type="text",
        tags=tags,
        content_sha=content_sha,
        file_path=None,
        text_content=text,
    )
    assert item_id == item_id_again

    items = list_items(limit=10)
    assert len(items) == 1
    assert items[0]["tags"] == ["alpha", "test"]
