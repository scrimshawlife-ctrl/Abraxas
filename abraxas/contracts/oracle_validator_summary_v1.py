from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class OracleValidatorSummaryV1:
    run_id: str
    lane: str
    status: str
    authority_item_count: int
    advisory_attachment_count: int
    not_computable_attachments: Sequence[str]
    artifact_refs: Sequence[str]
    hashes: dict[str, str]

    def to_dict(self) -> dict:
        return {
            "schema_id": "OracleValidatorSummary.v1",
            "run_id": self.run_id,
            "lane": self.lane,
            "status": self.status,
            "authority_item_count": self.authority_item_count,
            "advisory_attachment_count": self.advisory_attachment_count,
            "not_computable_attachments": list(self.not_computable_attachments),
            "artifact_refs": list(self.artifact_refs),
            "hashes": dict(self.hashes),
            "boundary_confirmation": "AUTHORITY_CORE_IMMUTABLE_FROM_ADVISORY",
        }
