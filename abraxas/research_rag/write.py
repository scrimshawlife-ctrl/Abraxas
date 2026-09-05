"""Idempotent ingest write path against Notion receipts and chunks."""

from __future__ import annotations

from typing import Sequence

from abraxas.research_rag.config import ResearchRagConfig
from abraxas.research_rag.errors import EmbedForbiddenError, IngestWriteError
from abraxas.research_rag.filters import (
    active_receipts_filter,
    chunks_for_receipt_filter,
    receipt_idempotency_filter,
)
from abraxas.research_rag.hashing import chunk_content_hash, chunk_id_for, payload_content_hash
from abraxas.research_rag.logging_util import log_fail
from abraxas.research_rag.notion_props import (
    checkbox_prop,
    chunk_properties,
    number_prop,
    parse_chunk,
    parse_receipt,
    receipt_properties,
    relation_prop,
    rich_text_prop,
    select_prop,
)
from abraxas.research_rag.registry_gate import resolve_registered_source
from abraxas.research_rag.store import NotionStore
from abraxas.research_rag.types import (
    EMBED_MODEL_NONE,
    ChunkRecord,
    ChunkStatus,
    IngestChunkSpec,
    IngestRequest,
    IngestResult,
    ReceiptRecord,
    ReceiptStatus,
    RegistryHit,
)


def ingest(store: NotionStore, config: ResearchRagConfig, request: IngestRequest) -> IngestResult:
    source_id = str(request.source_id or "").strip()
    registry = resolve_registered_source(store, config.registry_data_source_id, source_id)
    _assert_embed_none(EMBED_MODEL_NONE)
    payload_hash = payload_content_hash(request.payload)
    existing = _find_idempotent(store, config, source_id, payload_hash)
    if existing is not None:
        chunks = _chunks_for_receipt(store, config, existing.page_id)
        return IngestResult(
            outcome="existing",
            receipt=existing,
            chunks=chunks,
            superseded_receipt_ids=(),
            notes="idempotent_hit",
        )

    superseded_ids = _supersede_active(store, config, source_id)
    created_receipt_id = ""
    created_chunk_ids: list[str] = []
    try:
        receipt = _create_pending_receipt(store, config, request, registry, payload_hash)
        created_receipt_id = receipt.page_id
        chunks = _create_chunks(
            store, config, request, payload_hash, receipt.page_id, created_chunk_ids
        )
        receipt = _finalize_ok(store, receipt, chunks)
        return IngestResult(
            outcome="created",
            receipt=receipt,
            chunks=chunks,
            superseded_receipt_ids=superseded_ids,
        )
    except Exception as exc:
        _rollback(store, created_receipt_id, created_chunk_ids, exc)
        raise IngestWriteError(f"ingest_failed:{type(exc).__name__}") from exc


def _assert_embed_none(embed_model: str) -> None:
    if embed_model not in {"", EMBED_MODEL_NONE}:
        raise EmbedForbiddenError(f"embed_model_forbidden:{embed_model}")


def _find_idempotent(
    store: NotionStore, config: ResearchRagConfig, source_id: str, content_hash: str
) -> ReceiptRecord | None:
    pages = store.query_data_source(
        config.receipts_data_source_id,
        filter=receipt_idempotency_filter(source_id, content_hash),
        page_size=10,
    )
    if not pages:
        return None
    return parse_receipt(pages[0])


def _supersede_active(
    store: NotionStore, config: ResearchRagConfig, source_id: str
) -> tuple[str, ...]:
    pages = store.query_data_source(
        config.receipts_data_source_id,
        filter=active_receipts_filter(source_id),
        page_size=50,
    )
    superseded: list[str] = []
    for page in pages:
        receipt = parse_receipt(page)
        _archive_receipt_chunks(store, config, receipt.page_id)
        store.update_page(
            receipt.page_id,
            {
                "Status": select_prop(ReceiptStatus.SUPERSEDED.value),
                "Chunks": relation_prop(()),
                "Notes": rich_text_prop("superseded_by_hash_change"),
            },
        )
        superseded.append(receipt.page_id)
    return tuple(superseded)


def _archive_receipt_chunks(store: NotionStore, config: ResearchRagConfig, receipt_page_id: str) -> None:
    for chunk in _chunks_for_receipt(store, config, receipt_page_id):
        store.update_page(
            chunk.page_id,
            {
                "Status": select_prop(ChunkStatus.ARCHIVED.value),
                "Stale": checkbox_prop(True),
                "Ingest receipt": relation_prop(()),
            },
        )


def _chunks_for_receipt(
    store: NotionStore, config: ResearchRagConfig, receipt_page_id: str
) -> tuple[ChunkRecord, ...]:
    pages = store.query_data_source(
        config.chunks_data_source_id,
        filter=chunks_for_receipt_filter(receipt_page_id),
        page_size=100,
    )
    return tuple(parse_chunk(page) for page in pages)


def _create_pending_receipt(
    store: NotionStore,
    config: ResearchRagConfig,
    request: IngestRequest,
    registry: RegistryHit,
    payload_hash: str,
) -> ReceiptRecord:
    loop_names = [tag.value for tag in request.loop]
    name = f"{request.source_id} {payload_hash[:12]}"
    page = store.create_page(
        config.receipts_data_source_id,
        receipt_properties(
            name=name,
            source_id=request.source_id,
            registry_url=registry.page_url,
            content_hash=payload_hash,
            run_id=request.run_id,
            adapter=request.adapter,
            freshness=request.freshness,
            status=ReceiptStatus.PENDING,
            chunk_count=0,
            notes=request.notes,
            loop_names=loop_names,
            chunk_page_ids=(),
        ),
    )
    return parse_receipt(page)


def _create_chunks(
    store: NotionStore,
    config: ResearchRagConfig,
    request: IngestRequest,
    payload_hash: str,
    receipt_page_id: str,
    created_chunk_ids: list[str],
) -> tuple[ChunkRecord, ...]:
    loop_names = [tag.value for tag in request.loop]
    records: list[ChunkRecord] = []
    for index, spec in enumerate(request.chunks):
        record = _create_one_chunk(
            store, config, request.source_id, payload_hash, receipt_page_id, spec, index, loop_names
        )
        created_chunk_ids.append(record.page_id)
        records.append(record)
    return tuple(records)


def _create_one_chunk(
    store: NotionStore,
    config: ResearchRagConfig,
    source_id: str,
    payload_hash: str,
    receipt_page_id: str,
    spec: IngestChunkSpec,
    index: int,
    loop_names: Sequence[str],
) -> ChunkRecord:
    chunk_id = spec.chunk_id or chunk_id_for(source_id, payload_hash, index)
    content_hash = chunk_content_hash(spec.excerpt, spec.locator_url)
    page = store.create_page(
        config.chunks_data_source_id,
        chunk_properties(
            name=chunk_id,
            chunk_id=chunk_id,
            source_id=source_id,
            content_hash=content_hash,
            excerpt=spec.excerpt,
            locator_url=spec.locator_url,
            embed_model=EMBED_MODEL_NONE,
            status=ChunkStatus.RAW,
            stale=False,
            notes=spec.notes,
            loop_names=loop_names,
            receipt_page_ids=(receipt_page_id,),
        ),
    )
    return parse_chunk(page)


def _finalize_ok(
    store: NotionStore, receipt: ReceiptRecord, chunks: Sequence[ChunkRecord]
) -> ReceiptRecord:
    page = store.update_page(
        receipt.page_id,
        {
            "Status": select_prop(ReceiptStatus.OK.value),
            "Chunk count": number_prop(len(chunks)),
            "Chunks": relation_prop([chunk.page_id for chunk in chunks]),
        },
    )
    return parse_receipt(page)


def _rollback(
    store: NotionStore,
    receipt_page_id: str,
    chunk_page_ids: Sequence[str],
    exc: Exception,
) -> None:
    log_fail(
        "ingest_rollback",
        receipt_page_id=receipt_page_id,
        chunk_count=len(chunk_page_ids),
        error=type(exc).__name__,
    )
    for page_id in chunk_page_ids:
        store.update_page(
            page_id,
            {
                "Status": select_prop(ChunkStatus.ARCHIVED.value),
                "Stale": checkbox_prop(True),
                "Ingest receipt": relation_prop(()),
            },
        )
    if receipt_page_id:
        store.update_page(
            receipt_page_id,
            {
                "Status": select_prop(ReceiptStatus.FAILED.value),
                "Chunks": relation_prop(()),
                "Notes": rich_text_prop(f"failed:{type(exc).__name__}"),
            },
        )
