"""Set Chunk compile URL fields only. Never create or update Wiki pages."""

from __future__ import annotations

from typing import Any, Mapping

from abraxas.research_rag.config import ResearchRagConfig
from abraxas.research_rag.errors import CompileTargetError
from abraxas.research_rag.logging_util import log_fail
from abraxas.research_rag.notion_props import compile_url_properties, parse_chunk
from abraxas.research_rag.store import NotionStore
from abraxas.research_rag.types import ChunkRecord


def set_chunk_compile_urls(
    store: NotionStore,
    config: ResearchRagConfig,
    chunk_page_id: str,
    *,
    compile_source_url: str,
    wiki_claim_url: str,
) -> ChunkRecord:
    page_id = str(chunk_page_id or "").strip()
    if not page_id:
        raise CompileTargetError("missing_chunk_page_id")
    page = store.get_page(page_id)
    parent_id = _parent_data_source_id(page)
    if parent_id != config.chunks_data_source_id:
        log_fail(
            "compile_refused_non_chunk",
            page_id=page_id,
            parent_id=parent_id,
        )
        raise CompileTargetError(f"not_chunk_page:{page_id}")
    updated = store.update_page(
        page_id,
        compile_url_properties(compile_source_url, wiki_claim_url),
    )
    return parse_chunk(updated)


def _parent_data_source_id(page: Mapping[str, Any]) -> str:
    parent = page.get("parent")
    if not isinstance(parent, Mapping):
        return ""
    if parent.get("type") == "data_source_id" or parent.get("data_source_id"):
        return str(parent.get("data_source_id") or "")
    return ""
