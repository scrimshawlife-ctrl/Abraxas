from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


def _stable_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class MBOMRequest:
    request_id: str
    lifecycle_states: dict[str, str]
    domain_signals: list[str]
    resonance_score: float

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MBOMRequest":
        request_id = str(payload.get("request_id", "")).strip()
        lifecycle_states = payload.get("lifecycle_states", {})
        domain_signals = payload.get("domain_signals", [])
        resonance_score = float(payload.get("resonance_score", 0.0))

        if not request_id:
            raise ValueError("request_id is required")
        if not isinstance(lifecycle_states, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in lifecycle_states.items()
        ):
            raise ValueError("lifecycle_states must be dict[str,str]")
        if not isinstance(domain_signals, list) or not all(isinstance(item, str) for item in domain_signals):
            raise ValueError("domain_signals must be list[str]")

        return cls(
            request_id=request_id,
            lifecycle_states=lifecycle_states,
            domain_signals=domain_signals,
            resonance_score=resonance_score,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "lifecycle_states": dict(self.lifecycle_states),
            "domain_signals": list(self.domain_signals),
            "resonance_score": self.resonance_score,
        }


@dataclass(frozen=True)
class MBOMArtifact:
    schema_version: int
    subsystem: str
    lane: str
    request: MBOMRequest
    assessment: dict[str, Any]
    assessment_id: str
    status: str

    @classmethod
    def build(cls, request: MBOMRequest, assessment: dict[str, Any]) -> "MBOMArtifact":
        canonical = {
            "subsystem": "mbom_v1",
            "lane": "support",
            "request": request.to_dict(),
            "assessment": assessment,
        }
        assessment_id = hashlib.sha256(_stable_json(canonical).encode("utf-8")).hexdigest()
        return cls(
            schema_version=1,
            subsystem="mbom_v1",
            lane="support",
            request=request,
            assessment=assessment,
            assessment_id=assessment_id,
            status="mbom_assessment_emitted",
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MBOMArtifact":
        if int(payload.get("schema_version", 0)) != 1:
            raise ValueError("unsupported schema_version")
        if payload.get("subsystem") != "mbom_v1":
            raise ValueError("invalid subsystem")
        if payload.get("lane") != "support":
            raise ValueError("invalid lane")

        request = MBOMRequest.from_dict(payload.get("request", {}))
        assessment = payload.get("assessment", {})
        if not isinstance(assessment, dict):
            raise ValueError("assessment must be object")

        rebuilt = cls.build(request=request, assessment=assessment)
        if rebuilt.assessment_id != str(payload.get("assessment_id", "")):
            raise ValueError("assessment_id mismatch")

        return cls(
            schema_version=1,
            subsystem="mbom_v1",
            lane="support",
            request=request,
            assessment=assessment,
            assessment_id=rebuilt.assessment_id,
            status=str(payload.get("status", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "subsystem": self.subsystem,
            "lane": self.lane,
            "request": self.request.to_dict(),
            "assessment": dict(self.assessment),
            "assessment_id": self.assessment_id,
            "status": self.status,
        }
