"""Observed Notion data-source IDs and env-only secrets."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping

from abraxas.research_rag.errors import ConfigError

# Live DBs OBSERVED 2026-09-05 PT. Data sources are SoT, not SQLite/Chroma.
DEFAULT_RECEIPTS_DATA_SOURCE_ID = "5d4697c5-04cd-494a-aa10-d8eac2477dfb"
DEFAULT_CHUNKS_DATA_SOURCE_ID = "8781a2f5-928e-4355-8abc-7d0ef1f9da8d"
DEFAULT_REGISTRY_DATA_SOURCE_ID = "f17f06cb-a241-4c00-bc89-dd789b8f3759"
DEFAULT_NOTION_VERSION = "2025-09-03"
DEFAULT_TIMEOUT_S = 30.0
DEFAULT_MAX_RETRIES = 4

RECEIPTS_DATABASE_URL = "https://app.notion.com/p/61ab7ef2a8094b98963db683b4708068"
CHUNKS_DATABASE_URL = "https://app.notion.com/p/a09320d0c2c5400491246a4ec51bf32d"
REGISTRY_PAGE_URL = "https://app.notion.com/p/f878081da97e4c4ba5142af5c5337c1a"
REGISTRY_DATABASE_URL = "https://app.notion.com/p/f2a5cad35b01490582bd6c3ffe631cb5"
DOCTRINE_WIKI_URL = "https://app.notion.com/p/3d23e8ba2f5c81288fe4c5833598c795"


@dataclass(frozen=True)
class ResearchRagConfig:
    receipts_data_source_id: str = DEFAULT_RECEIPTS_DATA_SOURCE_ID
    chunks_data_source_id: str = DEFAULT_CHUNKS_DATA_SOURCE_ID
    registry_data_source_id: str = DEFAULT_REGISTRY_DATA_SOURCE_ID
    notion_version: str = DEFAULT_NOTION_VERSION
    timeout_s: float = DEFAULT_TIMEOUT_S
    max_retries: int = DEFAULT_MAX_RETRIES
    token: str = ""

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> ResearchRagConfig:
        env = os.environ if environ is None else environ
        return cls(
            receipts_data_source_id=_env(
                env, "ABX_RESEARCH_RAG_RECEIPTS_DATA_SOURCE", DEFAULT_RECEIPTS_DATA_SOURCE_ID
            ),
            chunks_data_source_id=_env(
                env, "ABX_RESEARCH_RAG_CHUNKS_DATA_SOURCE", DEFAULT_CHUNKS_DATA_SOURCE_ID
            ),
            registry_data_source_id=_env(
                env, "ABX_RESEARCH_RAG_REGISTRY_DATA_SOURCE", DEFAULT_REGISTRY_DATA_SOURCE_ID
            ),
            notion_version=_env(env, "NOTION_VERSION", DEFAULT_NOTION_VERSION),
            timeout_s=_env_float(env, "ABX_RESEARCH_RAG_TIMEOUT_S", DEFAULT_TIMEOUT_S),
            max_retries=_env_int(env, "ABX_RESEARCH_RAG_MAX_RETRIES", DEFAULT_MAX_RETRIES),
            token=str(env.get("NOTION_TOKEN") or "").strip(),
        )

    def require_token(self) -> str:
        if not self.token:
            raise ConfigError("NOTION_TOKEN missing")
        return self.token


def _env(environ: Mapping[str, str], key: str, default: str) -> str:
    value = str(environ.get(key) or "").strip()
    return value or default


def _env_float(environ: Mapping[str, str], key: str, default: float) -> float:
    raw = str(environ.get(key) or "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ConfigError(f"invalid_float:{key}") from exc


def _env_int(environ: Mapping[str, str], key: str, default: int) -> int:
    raw = str(environ.get(key) or "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"invalid_int:{key}") from exc
