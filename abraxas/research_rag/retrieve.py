"""Notion-native retrieve. No local BM25, SQLite, or Chroma cache."""

from __future__ import annotations

from abraxas.research_rag.config import ResearchRagConfig
from abraxas.research_rag.filters import retrieve_filter
from abraxas.research_rag.notion_props import notion_page_url, parse_chunk
from abraxas.research_rag.store import NotionStore
from abraxas.research_rag.types import ObservedHit, RetrieveQuery


def observed_label(source_id: str) -> str:
    return f"OBSERVED({source_id})"


def retrieve(
    store: NotionStore, config: ResearchRagConfig, query: RetrieveQuery
) -> tuple[ObservedHit, ...]:
    pages = store.query_data_source(
        config.chunks_data_source_id,
        filter=retrieve_filter(query),
        page_size=max(1, int(query.page_size)),
    )
    hits: list[ObservedHit] = []
    for page in pages:
        chunk = parse_chunk(page)
        receipt_id = chunk.receipt_page_ids[0] if chunk.receipt_page_ids else ""
        hits.append(
            ObservedHit(
                label=observed_label(chunk.source_id),
                source_id=chunk.source_id,
                excerpt=chunk.excerpt,
                chunk_id=chunk.chunk_id,
                status=chunk.status.value,
                chunk_page_url=chunk.page_url,
                receipt_page_url=notion_page_url(receipt_id) if receipt_id else "",
            )
        )
    return tuple(hits)
