from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OracleAdvisoryAttachmentV1:
    attachment_id: str
    status: str
    computable: bool
    payload: dict[str, Any]
    provenance: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": "OracleAdvisoryAttachment.v1",
            "attachment_id": self.attachment_id,
            "status": self.status,
            "computable": self.computable,
            "advisory_marker": "advisory_only",
            "payload": dict(self.payload),
            "provenance": dict(self.provenance),
        }
