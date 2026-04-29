from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, TypedDict


class ProposedAction(TypedDict):
    action_id: str
    action_type: str
    target_path: str
    rationale: str
    risk_level: str
    requires_operator_review: bool


class RepairManifest(TypedDict):
    schema_version: str
    manifest_id: str
    created_at: str
    source_run_id: str
    readiness_status: str
    design_pass_allowed: bool
    execution_allowed: bool
    runtime_mutation_allowed: bool
    proposed_actions: List[ProposedAction]
    safety: Dict[str, bool]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
