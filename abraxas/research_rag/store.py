"""Notion store protocol used by write, retrieve, and compile paths."""

from __future__ import annotations

from typing import Any, Mapping, Protocol


class NotionStore(Protocol):
    def query_data_source(
        self,
        data_source_id: str,
        *,
        filter: Mapping[str, Any] | None = None,
        page_size: int = 100,
    ) -> list[dict[str, Any]]:
        """Return pages from a Notion data source query."""

    def create_page(self, data_source_id: str, properties: Mapping[str, Any]) -> dict[str, Any]:
        """Create a page under a data source."""

    def update_page(self, page_id: str, properties: Mapping[str, Any]) -> dict[str, Any]:
        """Patch page properties. Does not create Wiki pages."""

    def get_page(self, page_id: str) -> dict[str, Any]:
        """Fetch a page for parent checks."""
