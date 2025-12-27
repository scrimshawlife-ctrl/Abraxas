# Typed Op Contracts (v0.1) — TypedDict declarations for rune payloads/results

from typing import Any, Dict, List, NotRequired, Optional, TypedDict


class ProvenanceBundle(TypedDict, total=False):
    timestamp_utc: str
    repo_commit: str
    config_sha256: str
    runtime_fingerprint: Dict[str, Any]
    seed: Optional[int]


class CompressionDetectPayload(TypedDict, total=False):
    text_event: str
    config: Dict[str, Any]
    seed: NotRequired[int]


class CompressionDetectResult(TypedDict, total=False):
    compression_event: Dict[str, Any]
    metrics: Dict[str, Any]
    labels: List[str]
    confidence: Optional[float]


class InfraSelfHealPayload(TypedDict, total=False):
    health_state: Dict[str, Any]
    policy: Dict[str, Any]
    audit_report_sha256: NotRequired[str]
    seed: NotRequired[int]


class InfraSelfHealResult(TypedDict, total=False):
    issues: List[str]
    action_plan: List[Dict[str, Any]]
    evidence: Dict[str, Any]
    audit_log: Dict[str, Any]


class ActuatorApplyPayload(TypedDict, total=False):
    action_plan: List[Dict[str, Any]]
    governance_receipt_id: str
    dry_run: NotRequired[bool]
    seed: NotRequired[int]


class ActuatorApplyResult(TypedDict, total=False):
    apply_receipt: Dict[str, Any]
    verification: Dict[str, Any]
    audit_log: List[Dict[str, Any]]
