"""Bulk pull plan schema for manifest-first acquisition."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex


class PlanStep(BaseModel):
    step_id: str
    action: str
    url_or_key: str
    expected_bytes: Optional[int] = None
    cache_policy: str = "REQUIRED"
    codec_hint: Optional[str] = None
    notes: Optional[str] = None
    deterministic_order_index: int

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "action": self.action,
            "url_or_key": self.url_or_key,
            "expected_bytes": self.expected_bytes,
            "cache_policy": self.cache_policy,
            "codec_hint": self.codec_hint,
            "notes": self.notes,
            "deterministic_order_index": self.deterministic_order_index,
        }


class BulkPullPlan(BaseModel):
    plan_id: str
    source_id: str
    created_at_utc: str
    window_utc: Dict[str, Optional[str]] = Field(default_factory=dict)
    manifest_id: str
    steps: List[PlanStep]

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "source_id": self.source_id,
            "created_at_utc": self.created_at_utc,
            "window_utc": dict(self.window_utc),
            "manifest_id": self.manifest_id,
            "steps": [step.canonical_payload() for step in self.steps],
        }

    def plan_hash(self) -> str:
        return sha256_hex(canonical_json(self.canonical_payload()))

    @classmethod
    def build(
        cls,
        *,
        source_id: str,
        created_at_utc: str,
        window_utc: Dict[str, Optional[str]],
        manifest_id: str,
        steps: List[PlanStep],
    ) -> "BulkPullPlan":
        payload = {
            "source_id": source_id,
            "created_at_utc": created_at_utc,
            "window_utc": dict(window_utc),
            "manifest_id": manifest_id,
            "steps": [step.canonical_payload() for step in steps],
        }
        plan_id = sha256_hex(canonical_json(payload))
        return cls(
            plan_id=plan_id,
            source_id=source_id,
            created_at_utc=created_at_utc,
            window_utc=window_utc,
            manifest_id=manifest_id,
            steps=steps,
        )
