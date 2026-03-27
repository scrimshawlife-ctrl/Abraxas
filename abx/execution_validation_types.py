from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ExecutionValidationStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    INCOMPLETE = "incomplete"
    NOT_COMPUTABLE = "not_computable"


@dataclass(frozen=True)
class ExecutionValidationResult:
    run_id: str
    artifact_id: str
    status: ExecutionValidationStatus
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    ledger_record_ids: list[str] = field(default_factory=list)
    ledger_artifact_ids: list[str] = field(default_factory=list)
    correlation_pointers: list[str] = field(default_factory=list)
    checked_at: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload


__all__ = [
    "ExecutionValidationResult",
    "ExecutionValidationStatus",
]
