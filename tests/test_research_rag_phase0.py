"""Acceptance tests for Research RAG Phase 0 (mocked Notion)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from abraxas.research_rag.compile import set_chunk_compile_urls
from abraxas.research_rag.config import ResearchRagConfig
from abraxas.research_rag.errors import (
    CompileTargetError,
    IngestWriteError,
    RetrieveQueryError,
    UnregisteredSourceError,
)
from abraxas.research_rag.filters import retrieve_filter
from abraxas.research_rag.hashing import payload_content_hash
from abraxas.research_rag.notion_http import NotionHttpStore, backoff_seconds
from abraxas.research_rag.notion_props import compile_url_properties, parse_chunk, parse_receipt
from abraxas.research_rag.retrieve import observed_label, retrieve
from abraxas.research_rag.types import (
    EMBED_MODEL_NONE,
    ChunkStatus,
    IngestChunkSpec,
    IngestRequest,
    ReceiptStatus,
    RetrieveQuery,
)
from abraxas.research_rag.write import ingest
from tests.research_rag.fake_notion import FakeNotionStore, create_count_for, updated_keys

RECEIPTS_DS = "receipts-ds"
CHUNKS_DS = "chunks-ds"
REGISTRY_DS = "registry-ds"
WIKI_DS = "wiki-ds"
SOURCE_ID = "WORLDBANK_REGION_V2"


def _config() -> ResearchRagConfig:
    return ResearchRagConfig(
        receipts_data_source_id=RECEIPTS_DS,
        chunks_data_source_id=CHUNKS_DS,
        registry_data_source_id=REGISTRY_DS,
    )


def _request(payload: str, excerpt: str, run_id: str = "run-1") -> IngestRequest:
    return IngestRequest(
        source_id=SOURCE_ID,
        payload=payload,
        run_id=run_id,
        adapter="worldbank_region_v2",
        freshness="2026-09-05",
        chunks=[IngestChunkSpec(excerpt=excerpt, locator_url="https://example.com/loc")],
    )


def _seeded_store() -> FakeNotionStore:
    store = FakeNotionStore()
    store.seed_registry(REGISTRY_DS, SOURCE_ID, name="World Bank regions")
    return store


def test_duplicate_hash_returns_existing_without_new_rows() -> None:
    store = _seeded_store()
    config = _config()
    first = ingest(store, config, _request("same-payload", "alpha excerpt"))
    created_receipts = create_count_for(store, RECEIPTS_DS)
    created_chunks = create_count_for(store, CHUNKS_DS)
    second = ingest(store, config, _request("same-payload", "alpha excerpt", run_id="run-2"))

    assert first.outcome == "created"
    assert second.outcome == "existing"
    assert second.receipt is not None
    assert first.receipt is not None
    assert second.receipt.page_id == first.receipt.page_id
    assert second.receipt.content_hash == payload_content_hash("same-payload")
    assert create_count_for(store, RECEIPTS_DS) == created_receipts
    assert create_count_for(store, CHUNKS_DS) == created_chunks


def test_hash_change_supersedes_prior_receipt_and_archives_chunks() -> None:
    store = _seeded_store()
    config = _config()
    first = ingest(store, config, _request("payload-v1", "first excerpt"))
    second = ingest(store, config, _request("payload-v2", "second excerpt", run_id="run-2"))

    assert first.receipt is not None
    assert second.outcome == "created"
    assert first.receipt.page_id in second.superseded_receipt_ids
    prior = parse_receipt(store.get_page(first.receipt.page_id))
    assert prior.status == ReceiptStatus.SUPERSEDED
    assert prior.chunk_page_ids == ()
    prior_chunk = parse_chunk(store.get_page(first.chunks[0].page_id))
    assert prior_chunk.status == ChunkStatus.ARCHIVED
    assert prior_chunk.stale is True
    assert prior_chunk.receipt_page_ids == ()
    assert second.receipt is not None
    assert second.receipt.status == ReceiptStatus.OK
    assert second.chunks[0].status == ChunkStatus.RAW
    assert second.chunks[0].embed_model == EMBED_MODEL_NONE
    assert second.chunks[0].stale is False
    assert retrieve(store, config, RetrieveQuery(excerpt_contains="first excerpt")) == ()
    updated_hits = retrieve(store, config, RetrieveQuery(excerpt_contains="second excerpt"))
    assert len(updated_hits) == 1
    assert updated_hits[0].label == f"OBSERVED({SOURCE_ID})"


def test_unregistered_source_refuses_without_writes() -> None:
    store = FakeNotionStore()
    with pytest.raises(UnregisteredSourceError) as err:
        ingest(store, _config(), _request("payload", "excerpt"))
    assert err.value.source_id == SOURCE_ID
    assert store.create_calls == []
    assert store.update_calls == []


def test_compile_sets_url_fields_only_and_never_writes_wiki() -> None:
    store = _seeded_store()
    result = ingest(store, _config(), _request("payload", "excerpt"))
    chunk_id = result.chunks[0].page_id
    wiki_creates_before = create_count_for(store, WIKI_DS)
    updated = set_chunk_compile_urls(
        store,
        _config(),
        chunk_id,
        compile_source_url="https://example.com/compile",
        wiki_claim_url="https://app.notion.com/p/3d23e8ba2f5c81288fe4c5833598c795",
    )
    assert updated.compile_source_url == "https://example.com/compile"
    assert "3d23e8ba2f5c81288fe4c5833598c795" in updated.wiki_claim_url
    assert create_count_for(store, WIKI_DS) == wiki_creates_before
    assert updated_keys(store, chunk_id)[-1] == {"Compile Source", "Wiki claim"}
    assert set(compile_url_properties("a", "b")) == {"Compile Source", "Wiki claim"}


def test_compile_refuses_non_chunk_parent() -> None:
    store = _seeded_store()
    wiki_page = store.create_page(WIKI_DS, {"Name": {"title": [{"text": {"content": "wiki"}}]}})
    with pytest.raises(CompileTargetError):
        set_chunk_compile_urls(
            store,
            _config(),
            wiki_page["id"],
            compile_source_url="https://example.com/compile",
            wiki_claim_url="https://example.com/claim",
        )


def test_retrieve_query_contract_and_observed_label() -> None:
    store = _seeded_store()
    ingest(store, _config(), _request("payload", "region catalog excerpt"))
    filt = retrieve_filter(RetrieveQuery(excerpt_contains="region", source_id=SOURCE_ID))
    assert "and" in filt
    hits = retrieve(store, _config(), RetrieveQuery(excerpt_contains="region", source_id=SOURCE_ID))
    assert len(hits) == 1
    assert hits[0].label == observed_label(SOURCE_ID)
    assert hits[0].label == f"OBSERVED({SOURCE_ID})"
    assert hits[0].chunk_page_url.startswith("https://www.notion.so/")
    assert hits[0].receipt_page_url.startswith("https://www.notion.so/")
    hidden = retrieve(store, _config(), RetrieveQuery(excerpt_contains="missing-term"))
    assert hidden == ()


def test_retrieve_requires_access_filter() -> None:
    with pytest.raises(RetrieveQueryError):
        retrieve_filter(RetrieveQuery())


def test_rollback_marks_failed_and_archives_partial_chunks() -> None:
    store = _seeded_store()
    store.fail_after_creates = 3
    request = IngestRequest(
        source_id=SOURCE_ID,
        payload="payload",
        run_id="run-1",
        adapter="worldbank_region_v2",
        freshness="2026-09-05",
        chunks=[
            IngestChunkSpec(excerpt="one", locator_url="https://example.com/a"),
            IngestChunkSpec(excerpt="two", locator_url="https://example.com/b"),
        ],
    )
    with pytest.raises(IngestWriteError):
        ingest(store, _config(), request)
    receipts = [
        parse_receipt(store.get_page(page_id))
        for page_id, page in store.pages.items()
        if page["parent"]["data_source_id"] == RECEIPTS_DS
    ]
    chunks = [
        parse_chunk(store.get_page(page_id))
        for page_id, page in store.pages.items()
        if page["parent"]["data_source_id"] == CHUNKS_DS
    ]
    assert receipts[0].status == ReceiptStatus.FAILED
    assert receipts[0].chunk_page_ids == ()
    assert "failed:" in receipts[0].notes
    assert chunks[0].status == ChunkStatus.ARCHIVED
    assert chunks[0].stale is True
    assert chunks[0].receipt_page_ids == ()


def test_created_chunk_embed_model_is_none() -> None:
    store = _seeded_store()
    result = ingest(store, _config(), _request("payload", "excerpt"))
    assert result.chunks[0].embed_model == "none"


def test_http_retries_on_429_then_succeeds() -> None:
    sleeps: list[float] = []
    calls = {"n": 0}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self) -> bytes:
            return json.dumps({"id": "ok", "properties": {}}).encode("utf-8")

    def _urlopen(request, timeout=30):
        calls["n"] += 1
        if calls["n"] == 1:
            import urllib.error

            raise urllib.error.HTTPError(request.full_url, 429, "rate", {}, None)
        return _Resp()

    client = NotionHttpStore(
        ResearchRagConfig(token="test-token", max_retries=3, timeout_s=5),
        urlopen=_urlopen,
        sleeper=sleeps.append,
    )
    payload = client.get_page("page-1")
    assert payload["id"] == "ok"
    assert calls["n"] == 2
    assert sleeps == [backoff_seconds(0)]


def test_cli_ingest_payload_shape(tmp_path: Path) -> None:
    from abraxas.research_rag.cli import _load_ingest_request

    path = tmp_path / "payload.json"
    path.write_text(
        json.dumps(
            {
                "payload": {"rows": [1]},
                "chunks": [{"excerpt": "one", "locator_url": "https://example.com/a"}],
            }
        ),
        encoding="utf-8",
    )
    args = type(
        "Args",
        (),
        {
            "source_id": SOURCE_ID,
            "run_id": "r1",
            "adapter": "adapter",
            "freshness": "2026-09-05",
            "payload_file": path,
            "notes": "",
        },
    )()
    request = _load_ingest_request(args)
    assert request.chunks[0].excerpt == "one"
    assert request.source_id == SOURCE_ID
