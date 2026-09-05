"""In-memory Notion store for Research RAG Phase 0 tests."""

from __future__ import annotations

from typing import Any, Mapping
from urllib.parse import urlparse

from abraxas.research_rag.notion_props import page_properties, plain_text, relation_ids


class FakeNotionStore:
    def __init__(self) -> None:
        self.pages: dict[str, dict[str, Any]] = {}
        self._by_source: dict[str, list[str]] = {}
        self._seq = 0
        self.create_calls: list[tuple[str, dict[str, Any]]] = []
        self.update_calls: list[tuple[str, dict[str, Any]]] = []
        self.fail_after_creates: int | None = None

    def seed_registry(self, data_source_id: str, source_id: str, name: str = "") -> str:
        return self.create_page(
            data_source_id,
            {
                "Name": {"title": [{"type": "text", "text": {"content": name or source_id}}]},
                "Source ID": {"rich_text": [{"type": "text", "text": {"content": source_id}}]},
            },
        )["id"]

    def query_data_source(
        self,
        data_source_id: str,
        *,
        filter: Mapping[str, Any] | None = None,
        page_size: int = 100,
    ) -> list[dict[str, Any]]:
        matched = [
            self.pages[page_id]
            for page_id in self._by_source.get(data_source_id, [])
            if filter is None or _matches(self.pages[page_id], filter)
        ]
        return matched[:page_size]

    def create_page(self, data_source_id: str, properties: Mapping[str, Any]) -> dict[str, Any]:
        if self.fail_after_creates is not None and len(self.create_calls) >= self.fail_after_creates:
            raise RuntimeError("injected_create_failure")
        self._seq += 1
        page_id = f"00000000-0000-4000-8000-{self._seq:012d}"
        page = {
            "id": page_id,
            "url": f"https://www.notion.so/{page_id.replace('-', '')}",
            "parent": {"type": "data_source_id", "data_source_id": data_source_id},
            "properties": _copy_props(properties),
        }
        self.pages[page_id] = page
        self._by_source.setdefault(data_source_id, []).append(page_id)
        self.create_calls.append((data_source_id, _copy_props(properties)))
        return page

    def update_page(self, page_id: str, properties: Mapping[str, Any]) -> dict[str, Any]:
        page = self.pages[page_id]
        merged = dict(page["properties"])
        merged.update(_copy_props(properties))
        page["properties"] = merged
        self.update_calls.append((page_id, _copy_props(properties)))
        return page

    def get_page(self, page_id: str) -> dict[str, Any]:
        return self.pages[page_id]


def create_count_for(store: FakeNotionStore, data_source_id: str) -> int:
    return sum(1 for ds, _ in store.create_calls if ds == data_source_id)


def updated_keys(store: FakeNotionStore, page_id: str) -> list[set[str]]:
    return [set(props) for target, props in store.update_calls if target == page_id]


def is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _copy_props(properties: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): _copy(value) for key, value in properties.items()}


def _copy(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _copy(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_copy(item) for item in value]
    return value


def _matches(page: Mapping[str, Any], filt: Mapping[str, Any]) -> bool:
    if "and" in filt:
        return all(_matches(page, clause) for clause in filt["and"])
    if "or" in filt:
        return any(_matches(page, clause) for clause in filt["or"])
    props = page_properties(page)
    prop = props.get(str(filt.get("property") or ""))
    if "rich_text" in filt:
        text = plain_text(prop if isinstance(prop, Mapping) else None)
        clause = filt["rich_text"]
        if "equals" in clause:
            return text == clause["equals"]
        if "contains" in clause:
            return str(clause["contains"]) in text
    if "select" in filt:
        text = plain_text(prop if isinstance(prop, Mapping) else None)
        return text == filt["select"]["equals"]
    if "relation" in filt:
        ids = relation_ids(prop if isinstance(prop, Mapping) else None)
        return filt["relation"]["contains"] in ids
    return False
