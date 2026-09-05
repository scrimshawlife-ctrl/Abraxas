"""Fail-closed External Source Registry lookup."""

from __future__ import annotations

from abraxas.research_rag.errors import UnregisteredSourceError
from abraxas.research_rag.filters import registry_source_filter
from abraxas.research_rag.logging_util import log_fail
from abraxas.research_rag.notion_props import notion_page_url, page_properties, plain_text
from abraxas.research_rag.store import NotionStore
from abraxas.research_rag.types import RegistryHit


def resolve_registered_source(
    store: NotionStore,
    registry_data_source_id: str,
    source_id: str,
) -> RegistryHit:
    cleaned = str(source_id or "").strip()
    if not cleaned:
        log_fail("unregistered_source", source_id=source_id, reason="empty")
        raise UnregisteredSourceError(source_id)
    pages = store.query_data_source(
        registry_data_source_id,
        filter=registry_source_filter(cleaned),
        page_size=5,
    )
    if not pages:
        log_fail("unregistered_source", source_id=cleaned, registry=registry_data_source_id)
        raise UnregisteredSourceError(cleaned)
    page = pages[0]
    page_id = str(page.get("id") or "")
    props = page_properties(page)
    return RegistryHit(
        source_id=cleaned,
        page_id=page_id,
        page_url=notion_page_url(page_id, page),
        name=plain_text(props.get("Name")) or plain_text(props.get("Connector Name")),
    )
