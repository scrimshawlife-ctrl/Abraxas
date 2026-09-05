"""Notion query filters for registry, ingest idempotency, and retrieve."""

from __future__ import annotations

from typing import Any, Sequence

from abraxas.research_rag.types import ChunkStatus, ReceiptStatus, RetrieveQuery
from abraxas.research_rag.errors import RetrieveQueryError


def rich_text_equals(property_name: str, value: str) -> dict[str, Any]:
    return {"property": property_name, "rich_text": {"equals": value}}


def rich_text_contains(property_name: str, value: str) -> dict[str, Any]:
    return {"property": property_name, "rich_text": {"contains": value}}


def select_equals(property_name: str, value: str) -> dict[str, Any]:
    return {"property": property_name, "select": {"equals": value}}


def relation_contains(property_name: str, page_id: str) -> dict[str, Any]:
    return {"property": property_name, "relation": {"contains": page_id}}


def or_filter(clauses: Sequence[dict[str, Any]]) -> dict[str, Any]:
    return {"or": list(clauses)}


def and_filter(clauses: Sequence[dict[str, Any]]) -> dict[str, Any]:
    return {"and": list(clauses)}


def source_id_filter(source_id: str) -> dict[str, Any]:
    return rich_text_equals("Source ID", source_id)


def registry_source_filter(source_id: str) -> dict[str, Any]:
    return source_id_filter(source_id)


def receipt_idempotency_filter(source_id: str, content_hash: str) -> dict[str, Any]:
    return and_filter(
        [
            source_id_filter(source_id),
            rich_text_equals("Content hash", content_hash),
            or_filter(
                [
                    select_equals("Status", ReceiptStatus.PENDING.value),
                    select_equals("Status", ReceiptStatus.OK.value),
                ]
            ),
        ]
    )


def active_receipts_filter(source_id: str) -> dict[str, Any]:
    return and_filter(
        [
            source_id_filter(source_id),
            or_filter(
                [
                    select_equals("Status", ReceiptStatus.PENDING.value),
                    select_equals("Status", ReceiptStatus.OK.value),
                ]
            ),
        ]
    )


def chunks_for_receipt_filter(receipt_page_id: str) -> dict[str, Any]:
    return relation_contains("Ingest receipt", receipt_page_id)


def retrieve_filter(query: RetrieveQuery) -> dict[str, Any]:
    excerpt = str(query.excerpt_contains or "").strip()
    source_id = str(query.source_id or "").strip()
    access: list[dict[str, Any]] = []
    if excerpt:
        access.append(rich_text_contains("Excerpt", excerpt))
    if source_id:
        access.append(source_id_filter(source_id))
    if not access:
        raise RetrieveQueryError("retrieve requires excerpt_contains and/or source_id")

    status_clause = or_filter(
        [select_equals("Status", status.value) for status in (ChunkStatus.RAW, ChunkStatus.INDEXED)]
    )
    if len(access) == 1:
        return and_filter([status_clause, access[0]])
    return and_filter([status_clause, and_filter(access)])
