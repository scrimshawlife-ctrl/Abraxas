"""Typed fail-closed errors for Research RAG Phase 0."""

from __future__ import annotations


class ResearchRagError(Exception):
    """Base error for the research_rag package."""


class ConfigError(ResearchRagError):
    """Missing or invalid operator configuration."""


class UnregisteredSourceError(ResearchRagError):
    """Source ID is not present in the External Source Registry."""

    def __init__(self, source_id: str) -> None:
        self.source_id = source_id
        super().__init__(f"unregistered_source:{source_id}")


class RetrieveQueryError(ResearchRagError):
    """Retrieve query is missing required access filters."""


class EmbedForbiddenError(ResearchRagError):
    """Phase 0 forbids paid or non-none embed models."""


class CompileTargetError(ResearchRagError):
    """Compile helper refused a non-chunk target."""


class IngestWriteError(ResearchRagError):
    """Ingest write failed after rollback was attempted."""


class NotionTransportError(ResearchRagError):
    """Notion HTTP transport failed after retries."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        self.status_code = status_code
        super().__init__(message)
