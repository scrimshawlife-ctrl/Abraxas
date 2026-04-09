from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence


@dataclass(frozen=True)
class OracleSignalLayerOutputV2:
    run_id: str
    lane: str
    authority: dict[str, Any]
    advisory_attachments: Sequence[dict[str, Any]]
    boundary_enforced: bool
    provenance: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": "OracleSignalLayerOutput.v2",
            "run_id": self.run_id,
            "lane": self.lane,
            "authority": dict(self.authority),
            "advisory_attachments": list(self.advisory_attachments),
            "authority_advisory_boundary_enforced": self.boundary_enforced,
            "provenance": dict(self.provenance),
        }
