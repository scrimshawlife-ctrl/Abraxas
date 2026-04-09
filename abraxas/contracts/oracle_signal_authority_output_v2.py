from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence


@dataclass(frozen=True)
class OracleSignalAuthorityOutputV2:
    run_id: str
    lane: str
    items: Sequence[dict[str, Any]]
    authority_scope: str
    provenance: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": "OracleSignalAuthorityOutput.v2",
            "run_id": self.run_id,
            "lane": self.lane,
            "authority_scope": self.authority_scope,
            "signal_items": list(self.items),
            "provenance": dict(self.provenance),
        }
