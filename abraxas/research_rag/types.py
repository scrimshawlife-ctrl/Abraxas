"""Live Notion enum and record types for Research RAG Phase 0.

Enums match OBSERVED 2026-09-05 PT Ingest Receipts and Research Chunks
data-source schemas. This surface is advisory access, not Canon.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence, Union


class ReceiptStatus(str, Enum):
    PENDING = "pending"
    OK = "ok"
    FAILED = "failed"
    SUPERSEDED = "superseded"


class ChunkStatus(str, Enum):
    RAW = "raw"
    INDEXED = "indexed"
    STALE = "stale"
    ARCHIVED = "archived"


class LoopTag(str, Enum):
    COMPILER = "compiler"
    TIMECHAIN = "timechain"
    CHRONO = "chrono"
    ELECTION = "election"


EMBED_MODEL_NONE = "none"
RETRIEVE_CHUNK_STATUSES = (ChunkStatus.RAW, ChunkStatus.INDEXED)
ACTIVE_RECEIPT_STATUSES = (ReceiptStatus.PENDING, ReceiptStatus.OK)

Payload = Union[str, bytes, Mapping[str, object]]


@dataclass(frozen=True)
class IngestChunkSpec:
    excerpt: str
    locator_url: str = ""
    chunk_id: str = ""
    notes: str = ""


@dataclass(frozen=True)
class IngestRequest:
    source_id: str
    payload: Payload
    run_id: str
    adapter: str
    freshness: str
    chunks: Sequence[IngestChunkSpec]
    loop: Sequence[LoopTag] = ()
    notes: str = ""


@dataclass(frozen=True)
class RegistryHit:
    source_id: str
    page_id: str
    page_url: str
    name: str


@dataclass(frozen=True)
class ReceiptRecord:
    page_id: str
    page_url: str
    source_id: str
    content_hash: str
    status: ReceiptStatus
    run_id: str
    chunk_page_ids: tuple[str, ...]
    chunk_count: int
    notes: str = ""


@dataclass(frozen=True)
class ChunkRecord:
    page_id: str
    page_url: str
    chunk_id: str
    source_id: str
    excerpt: str
    status: ChunkStatus
    content_hash: str
    receipt_page_ids: tuple[str, ...]
    stale: bool
    embed_model: str
    compile_source_url: str = ""
    wiki_claim_url: str = ""
    locator_url: str = ""


@dataclass(frozen=True)
class IngestResult:
    outcome: str
    receipt: ReceiptRecord | None
    chunks: tuple[ChunkRecord, ...]
    superseded_receipt_ids: tuple[str, ...]
    notes: str = ""


@dataclass(frozen=True)
class RetrieveQuery:
    excerpt_contains: str = ""
    source_id: str = ""
    page_size: int = 50


@dataclass(frozen=True)
class ObservedHit:
    label: str
    source_id: str
    excerpt: str
    chunk_id: str
    status: str
    chunk_page_url: str
    receipt_page_url: str
