"""
ContinuityLedgerEntry.v0

Deterministic, hashable append-only record describing the continuity
of FAMILIAR-mediated runs across time.

Rules:
- Append-only semantics (enforced by writer, not here).
- No semantic interpretation of deltas.
- Used for stabilization windows and audit trails.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import hashlib
import json


# -------------------------
# Helpers
# -------------------------

def _stable_json(data: Dict[str, Any]) -> str:
    return json.dumps(
        data,
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
    )


def _hash_payload(payload: Dict[str, Any]) -> str:
    stable = _stable_json(payload)
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()


# -------------------------
# IR Definition
# -------------------------

@dataclass(frozen=True)
class ContinuityLedgerEntry:
    """
    ContinuityLedgerEntry.v0

    Describes one completed (or halted) run and its relationship
    to prior runs.
    """

    run_id: str

    input_hash: str
    task_graph_hash: str
    invocation_plan_hash: Optional[str] = None
    output_hash: Optional[str] = None

    # Delta information relative to a prior run (if any)
    prior_run_id: Optional[str] = None
    delta_summary: Optional[str] = None

    stabilization_cycle: int = 0

    meta: Dict[str, Any] = field(default_factory=dict)

    not_computable: bool = False
    missing_fields: List[str] = field(default_factory=list)

    def validate(self) -> None:
        if not self.run_id:
            raise ValueError("run_id must be non-empty")

        if not self.input_hash:
            raise ValueError("input_hash must be non-empty")

        if not self.task_graph_hash:
            raise ValueError("task_graph_hash must be non-empty")

        if self.stabilization_cycle < 0:
            raise ValueError("stabilization_cycle must be non-negative")

        if not isinstance(self.meta, dict):
            raise ValueError("meta must be a dict")

        if self.not_computable and not self.missing_fields:
            raise ValueError("not_computable=True requires missing_fields to be non-empty")

    def to_payload(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "input_hash": self.input_hash,
            "task_graph_hash": self.task_graph_hash,
            "invocation_plan_hash": self.invocation_plan_hash,
            "output_hash": self.output_hash,
            "prior_run_id": self.prior_run_id,
            "delta_summary": self.delta_summary,
            "stabilization_cycle": self.stabilization_cycle,
            "meta": self.meta,
            "not_computable": self.not_computable,
            "missing_fields": list(self.missing_fields),
        }

    def hash(self) -> str:
        self.validate()
        return _hash_payload(self.to_payload())

    def semantically_equal(self, other: "ContinuityLedgerEntry") -> bool:
        if not isinstance(other, ContinuityLedgerEntry):
            return False
        return self.hash() == other.hash()
