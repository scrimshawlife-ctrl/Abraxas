"""SourceAtlas registry, adapters, and discovery tooling."""

from .atlas import atlas_version, build_source_atlas, get_source, list_sources, resolve_sources
from .discovery import discover_sources
from .scheduler import CadencePlan, build_cadence_plan
from .types import (
    CandidateSourceRecord,
    Cadence,
    CachePolicy,
    SourceAccess,
    SourceCoverage,
    SourceId,
    SourceKind,
    SourcePacket,
    SourceProvenance,
    SourceRecord,
    SourceRef,
    SourceSpec,
    SourceWindow,
)
from .packets import SourcePacket as Packet

__all__ = [
    "atlas_version",
    "build_source_atlas",
    "get_source",
    "list_sources",
    "resolve_sources",
    "discover_sources",
    "build_cadence_plan",
    "CadencePlan",
    "CandidateSourceRecord",
    "Cadence",
    "CachePolicy",
    "SourceAccess",
    "SourceCoverage",
    "SourceId",
    "SourceKind",
    "SourcePacket",
    "SourceProvenance",
    "SourceRecord",
    "SourceRef",
    "SourceSpec",
    "SourceWindow",
    "Packet",
]
