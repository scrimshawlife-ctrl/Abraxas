from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class OSHFetchJob:
    job_id: str
    run_id: str
    action_id: str
    url: str
    method: str
    params: Dict[str, Any]
    source_label: str
    vector_node_id: Optional[str]
    allowlist_source_id: Optional[str]
    budget: Dict[str, Any]
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RawFetchArtifact:
    artifact_id: str
    run_id: str
    job_id: str
    fetched_ts: str
    url: str
    status_code: int
    content_type: str
    body_path: str
    body_sha256: str
    meta: Dict[str, Any]
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
