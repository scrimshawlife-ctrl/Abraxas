from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OracleTrendAttachmentV1:
    status: str
    computable: bool
    payload: dict[str, Any]
    provenance: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": "OracleTrendAttachment.v1",
            "attachment_id": "trend",
            "status": self.status,
            "computable": self.computable,
            "advisory_marker": "advisory_only",
            "payload": dict(self.payload),
            "provenance": dict(self.provenance),
        }
