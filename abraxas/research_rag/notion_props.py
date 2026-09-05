"""Notion property builders and parsers for live Research RAG schemas."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from abraxas.research_rag.types import ChunkRecord, ChunkStatus, ReceiptRecord, ReceiptStatus

_TEXT_LIMIT = 2000


def clip_text(value: str, limit: int = _TEXT_LIMIT) -> str:
    text = str(value or "")
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def title_prop(value: str) -> dict[str, Any]:
    return {"title": [{"type": "text", "text": {"content": clip_text(value)}}]}


def rich_text_prop(value: str) -> dict[str, Any]:
    return {"rich_text": [{"type": "text", "text": {"content": clip_text(value)}}]}


def url_prop(value: str) -> dict[str, Any]:
    text = str(value or "").strip()
    return {"url": text or None}


def select_prop(name: str) -> dict[str, Any]:
    return {"select": {"name": str(name)}}


def checkbox_prop(value: bool) -> dict[str, Any]:
    return {"checkbox": bool(value)}


def number_prop(value: int) -> dict[str, Any]:
    return {"number": int(value)}


def date_prop(start: str) -> dict[str, Any]:
    return {"date": {"start": str(start)}}


def relation_prop(page_ids: Sequence[str]) -> dict[str, Any]:
    return {"relation": [{"id": str(page_id)} for page_id in page_ids]}


def multi_select_prop(names: Iterable[str]) -> dict[str, Any]:
    return {"multi_select": [{"name": str(name)} for name in names]}


def notion_page_url(page_id: str, page: Mapping[str, Any] | None = None) -> str:
    if page and page.get("url"):
        return str(page["url"])
    compact = str(page_id).replace("-", "")
    return f"https://www.notion.so/{compact}"


def plain_text(prop: Mapping[str, Any] | None) -> str:
    if not prop:
        return ""
    if prop.get("type") == "title" or "title" in prop:
        return _join_rich(prop.get("title") or [])
    if prop.get("type") == "rich_text" or "rich_text" in prop:
        return _join_rich(prop.get("rich_text") or [])
    if "url" in prop and prop.get("url"):
        return str(prop.get("url") or "")
    if "select" in prop and isinstance(prop.get("select"), Mapping):
        return str(prop["select"].get("name") or "")
    return ""


def checkbox_value(prop: Mapping[str, Any] | None) -> bool:
    if not prop:
        return False
    return bool(prop.get("checkbox"))


def number_value(prop: Mapping[str, Any] | None) -> int:
    if not prop:
        return 0
    raw = prop.get("number")
    if raw is None:
        return 0
    return int(raw)


def relation_ids(prop: Mapping[str, Any] | None) -> tuple[str, ...]:
    if not prop:
        return ()
    items = prop.get("relation") or []
    out: list[str] = []
    for item in items:
        if isinstance(item, Mapping) and item.get("id"):
            out.append(str(item["id"]))
    return tuple(out)


def page_properties(page: Mapping[str, Any]) -> Mapping[str, Any]:
    props = page.get("properties")
    if isinstance(props, Mapping):
        return props
    return {}


def parse_receipt(page: Mapping[str, Any]) -> ReceiptRecord:
    props = page_properties(page)
    page_id = str(page.get("id") or "")
    status_name = plain_text(props.get("Status")) or ReceiptStatus.PENDING.value
    return ReceiptRecord(
        page_id=page_id,
        page_url=notion_page_url(page_id, page),
        source_id=plain_text(props.get("Source ID")),
        content_hash=plain_text(props.get("Content hash")),
        status=ReceiptStatus(status_name),
        run_id=plain_text(props.get("Run ID")),
        chunk_page_ids=relation_ids(props.get("Chunks")),
        chunk_count=number_value(props.get("Chunk count")),
        notes=plain_text(props.get("Notes")),
    )


def parse_chunk(page: Mapping[str, Any]) -> ChunkRecord:
    props = page_properties(page)
    page_id = str(page.get("id") or "")
    status_name = plain_text(props.get("Status")) or ChunkStatus.RAW.value
    return ChunkRecord(
        page_id=page_id,
        page_url=notion_page_url(page_id, page),
        chunk_id=plain_text(props.get("Chunk ID")),
        source_id=plain_text(props.get("Source ID")),
        excerpt=plain_text(props.get("Excerpt")),
        status=ChunkStatus(status_name),
        content_hash=plain_text(props.get("Content hash")),
        receipt_page_ids=relation_ids(props.get("Ingest receipt")),
        stale=checkbox_value(props.get("Stale")),
        embed_model=plain_text(props.get("Embed model")),
        compile_source_url=plain_text(props.get("Compile Source")),
        wiki_claim_url=plain_text(props.get("Wiki claim")),
        locator_url=plain_text(props.get("Locator URL")),
    )


def receipt_properties(
    *,
    name: str,
    source_id: str,
    registry_url: str,
    content_hash: str,
    run_id: str,
    adapter: str,
    freshness: str,
    status: ReceiptStatus,
    chunk_count: int,
    notes: str = "",
    loop_names: Sequence[str] = (),
    chunk_page_ids: Sequence[str] | None = None,
) -> dict[str, Any]:
    props: dict[str, Any] = {
        "Name": title_prop(name),
        "Source ID": rich_text_prop(source_id),
        "Registry URL": url_prop(registry_url),
        "Content hash": rich_text_prop(content_hash),
        "Run ID": rich_text_prop(run_id),
        "Adapter": rich_text_prop(adapter),
        "Freshness": date_prop(freshness),
        "Status": select_prop(status.value),
        "Chunk count": number_prop(chunk_count),
        "Notes": rich_text_prop(notes),
    }
    if loop_names:
        props["Loop"] = multi_select_prop(loop_names)
    if chunk_page_ids is not None:
        props["Chunks"] = relation_prop(chunk_page_ids)
    return props


def chunk_properties(
    *,
    name: str,
    chunk_id: str,
    source_id: str,
    content_hash: str,
    excerpt: str,
    locator_url: str,
    embed_model: str,
    status: ChunkStatus,
    stale: bool,
    notes: str = "",
    loop_names: Sequence[str] = (),
    receipt_page_ids: Sequence[str] | None = None,
    compile_source_url: str | None = None,
    wiki_claim_url: str | None = None,
) -> dict[str, Any]:
    props: dict[str, Any] = {
        "Name": title_prop(name),
        "Chunk ID": rich_text_prop(chunk_id),
        "Source ID": rich_text_prop(source_id),
        "Content hash": rich_text_prop(content_hash),
        "Excerpt": rich_text_prop(excerpt),
        "Locator URL": url_prop(locator_url),
        "Embed model": rich_text_prop(embed_model),
        "Status": select_prop(status.value),
        "Stale": checkbox_prop(stale),
        "Notes": rich_text_prop(notes),
    }
    if loop_names:
        props["Loop"] = multi_select_prop(loop_names)
    if receipt_page_ids is not None:
        props["Ingest receipt"] = relation_prop(receipt_page_ids)
    if compile_source_url is not None:
        props["Compile Source"] = url_prop(compile_source_url)
    if wiki_claim_url is not None:
        props["Wiki claim"] = url_prop(wiki_claim_url)
    return props


def compile_url_properties(compile_source_url: str, wiki_claim_url: str) -> dict[str, Any]:
    return {
        "Compile Source": url_prop(compile_source_url),
        "Wiki claim": url_prop(wiki_claim_url),
    }


def _join_rich(items: Sequence[Any]) -> str:
    parts: list[str] = []
    for item in items:
        if not isinstance(item, Mapping):
            continue
        text = item.get("plain_text")
        if text:
            parts.append(str(text))
            continue
        inner = item.get("text")
        if isinstance(inner, Mapping):
            parts.append(str(inner.get("content") or ""))
    return "".join(parts)
