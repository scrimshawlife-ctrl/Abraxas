"""Operator CLI for Research RAG Phase 0. Secrets stay in env."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from enum import Enum
from pathlib import Path
from typing import Any, Sequence

from abraxas.core.canonical import canonical_json
from abraxas.research_rag.compile import set_chunk_compile_urls
from abraxas.research_rag.config import ResearchRagConfig
from abraxas.research_rag.errors import ResearchRagError
from abraxas.research_rag.notion_http import connect_from_env
from abraxas.research_rag.retrieve import retrieve
from abraxas.research_rag.types import IngestChunkSpec, IngestRequest, RetrieveQuery
from abraxas.research_rag.write import ingest


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m abraxas.research_rag",
        description="Abraxas Research RAG Phase 0: Notion write/retrieve. Not Canon.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    ingest_p = sub.add_parser("ingest", help="Idempotent receipt + chunk write")
    ingest_p.add_argument("--source-id", required=True)
    ingest_p.add_argument("--run-id", required=True)
    ingest_p.add_argument("--adapter", required=True)
    ingest_p.add_argument("--freshness", required=True, help="ISO date YYYY-MM-DD")
    ingest_p.add_argument("--payload-file", required=True, type=Path)
    ingest_p.add_argument("--notes", default="")

    retrieve_p = sub.add_parser("retrieve", help="Notion query/filter retrieve")
    retrieve_p.add_argument("--excerpt", default="")
    retrieve_p.add_argument("--source-id", default="")
    retrieve_p.add_argument("--page-size", type=int, default=50)

    compile_p = sub.add_parser("compile", help="Set Chunk compile URLs only")
    compile_p.add_argument("--chunk-page-id", required=True)
    compile_p.add_argument("--compile-source-url", required=True)
    compile_p.add_argument("--wiki-claim-url", required=True)

    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        config = ResearchRagConfig.from_env()
        store = connect_from_env()
        if args.command == "ingest":
            request = _load_ingest_request(args)
            result = ingest(store, config, request)
            _print(asdict(result))
            return 0 if result.outcome in {"existing", "created"} else 2
        if args.command == "retrieve":
            hits = retrieve(
                store,
                config,
                RetrieveQuery(
                    excerpt_contains=args.excerpt,
                    source_id=args.source_id,
                    page_size=args.page_size,
                ),
            )
            _print({"hits": [asdict(hit) for hit in hits]})
            return 0
        chunk = set_chunk_compile_urls(
            store,
            config,
            args.chunk_page_id,
            compile_source_url=args.compile_source_url,
            wiki_claim_url=args.wiki_claim_url,
        )
        _print(asdict(chunk))
        return 0
    except ResearchRagError as exc:
        _print({"status": "blocked", "error": str(exc)})
        return 2


def _load_ingest_request(args: argparse.Namespace) -> IngestRequest:
    raw = json.loads(Path(args.payload_file).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("payload_file_must_be_object")
    payload = raw.get("payload", raw)
    chunk_rows = raw.get("chunks") or []
    chunks = [
        IngestChunkSpec(
            excerpt=str(row.get("excerpt") or ""),
            locator_url=str(row.get("locator_url") or ""),
            chunk_id=str(row.get("chunk_id") or ""),
            notes=str(row.get("notes") or ""),
        )
        for row in chunk_rows
        if isinstance(row, dict)
    ]
    return IngestRequest(
        source_id=args.source_id,
        payload=payload if isinstance(payload, (str, dict)) else json.dumps(payload),
        run_id=args.run_id,
        adapter=args.adapter,
        freshness=args.freshness,
        chunks=chunks,
        notes=args.notes,
    )


def _print(payload: dict[str, Any]) -> None:
    sys.stdout.write(canonical_json(_jsonable(payload)) + "\n")


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value
