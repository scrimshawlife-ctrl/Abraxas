from __future__ import annotations

from dataclasses import dataclass, field
import json
import hashlib
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ContinuityLedgerEntry:
    run_id: str
    input_hash: str
    task_graph_hash: str
    invocation_plan_hash: str
    output_hash: Optional[str]
    prior_run_id: Optional[str]
    delta_summary: Optional[str]
    stabilization_cycle: int
    meta: Dict[str, Any] = field(default_factory=dict)
    not_computable: bool = False
    missing_fields: List[str] = field(default_factory=list)

    def hash(self) -> str:
        payload = json.dumps(
            {
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
                "missing_fields": self.missing_fields,
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
