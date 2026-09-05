# Research RAG Phase 0 — Notion write + retrieve

Shadow advisory access path. **Not Canon.** Notion databases are the system of record for ingest receipts and research chunks. Phase 0 does not use local BM25, SQLite, or Chroma, and it does not call paid embed APIs.

Operator stamp: Danny human-yes OBSERVED 2026-09-05 PT.

## Live data sources (OBSERVED)

| Surface | Page | Data source |
| --- | --- | --- |
| Ingest Receipts | https://app.notion.com/p/61ab7ef2a8094b98963db683b4708068 | `collection://5d4697c5-04cd-494a-aa10-d8eac2477dfb` |
| Research Chunks | https://app.notion.com/p/a09320d0c2c5400491246a4ec51bf32d | `collection://8781a2f5-928e-4355-8abc-7d0ef1f9da8d` |
| External Source Registry | https://app.notion.com/p/f878081da97e4c4ba5142af5c5337c1a | `collection://f17f06cb-a241-4c00-bc89-dd789b8f3759` |
| Doctrine Wiki (cite only) | https://app.notion.com/p/3d23e8ba2f5c81288fe4c5833598c795 | never written by this path |

Receipt status enum: `pending`, `ok`, `failed`, `superseded`.  
Chunk status enum: `raw`, `indexed`, `stale`, `archived`.  
Embed model field: empty or `none`.

## Environment

Secrets are env-only. Do not commit tokens.

```
NOTION_TOKEN=
NOTION_VERSION=2025-09-03
ABX_RESEARCH_RAG_RECEIPTS_DATA_SOURCE=5d4697c5-04cd-494a-aa10-d8eac2477dfb
ABX_RESEARCH_RAG_CHUNKS_DATA_SOURCE=8781a2f5-928e-4355-8abc-7d0ef1f9da8d
ABX_RESEARCH_RAG_REGISTRY_DATA_SOURCE=f17f06cb-a241-4c00-bc89-dd789b8f3759
ABX_RESEARCH_RAG_TIMEOUT_S=30
ABX_RESEARCH_RAG_MAX_RETRIES=4
```

See `.env.example`.

## Module and CLI

```bash
PYTHONPATH=. python -m abraxas.research_rag ingest \
  --source-id WORLDBANK_REGION_V2 \
  --run-id RUN-RAG-0001 \
  --adapter worldbank_region_v2 \
  --freshness 2026-09-05 \
  --payload-file path/to/payload.json

PYTHONPATH=. python -m abraxas.research_rag retrieve \
  --excerpt "region" \
  --source-id WORLDBANK_REGION_V2

PYTHONPATH=. python -m abraxas.research_rag compile \
  --chunk-page-id <chunk-page-uuid> \
  --compile-source-url https://example.com/compile \
  --wiki-claim-url https://app.notion.com/p/3d23e8ba2f5c81288fe4c5833598c795
```

`payload.json` shape:

```json
{
  "payload": {"opaque": "bytes-or-object hashed with sha256"},
  "chunks": [{"excerpt": "access text", "locator_url": "https://example.com/loc"}]
}
```

Library entrypoints: `abraxas.research_rag.ingest`, `retrieve`, `set_chunk_compile_urls`.

## Behavior

1. Source ID must resolve in External Source Registry or the write aborts with no Notion writes.
2. Idempotency key is Source ID + payload content hash. Same key returns the existing receipt.
3. Hash change marks prior receipt `superseded`, prior chunks `archived` + `Stale=true`, and clears relations, then writes a new receipt and chunks.
4. Retrieve is a Notion query/filter. Hits are labeled `OBSERVED(source)` and include receipt/chunk page URLs.
5. Compile helper patches Chunk `Compile Source` and `Wiki claim` URLs only.

## Validation

```bash
PYTHONPATH=. pytest -q tests/test_research_rag_phase0.py
make test-research-rag
make preflight-research_rag_v0
```

Status without live-run receipts: `partial` / `attestation_pending`. This package does not mint Canon, closure, or promotion.
