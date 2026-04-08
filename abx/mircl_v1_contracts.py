from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


def _stable_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class MirclRequest:
    request_id: str
    prompt: str
    context_tags: list[str]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MirclRequest":
        request_id = str(payload.get("request_id", "")).strip()
        prompt = str(payload.get("prompt", "")).strip()
        context_tags = payload.get("context_tags", [])

        if not request_id:
            raise ValueError("request_id is required")
        if not prompt:
            raise ValueError("prompt is required")
        if not isinstance(context_tags, list) or not all(isinstance(item, str) for item in context_tags):
            raise ValueError("context_tags must be list[str]")

        return cls(request_id=request_id, prompt=prompt, context_tags=context_tags)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "prompt": self.prompt,
            "context_tags": list(self.context_tags),
        }


@dataclass(frozen=True)
class MirclAdvisoryArtifact:
    schema_version: int
    subsystem: str
    lane: str
    request_id: str
    advisory_id: str
    source_prompt: str
    advisory_text: str
    context_tags: list[str]
    status: str

    @classmethod
    def build(cls, request: MirclRequest) -> "MirclAdvisoryArtifact":
        advisory_text = f"MIRCL shadow advisory for request {request.request_id}: {request.prompt}"
        advisory_id = hashlib.sha256(
            _stable_json(
                {
                    "subsystem": "mircl_v1",
                    "lane": "shadow",
                    "request": request.to_dict(),
                    "advisory_text": advisory_text,
                }
            ).encode("utf-8")
        ).hexdigest()
        return cls(
            schema_version=1,
            subsystem="mircl_v1",
            lane="shadow",
            request_id=request.request_id,
            advisory_id=advisory_id,
            source_prompt=request.prompt,
            advisory_text=advisory_text,
            context_tags=list(request.context_tags),
            status="shadow_advisory_emitted",
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MirclAdvisoryArtifact":
        if int(payload.get("schema_version", 0)) != 1:
            raise ValueError("unsupported schema_version")
        if payload.get("subsystem") != "mircl_v1":
            raise ValueError("invalid subsystem")
        if payload.get("lane") != "shadow":
            raise ValueError("invalid lane")

        request = MirclRequest(
            request_id=str(payload.get("request_id", "")),
            prompt=str(payload.get("source_prompt", "")),
            context_tags=list(payload.get("context_tags", [])),
        )
        rebuilt = cls.build(request)
        if rebuilt.advisory_id != str(payload.get("advisory_id", "")):
            raise ValueError("advisory_id mismatch")
        return cls(
            schema_version=1,
            subsystem="mircl_v1",
            lane="shadow",
            request_id=request.request_id,
            advisory_id=rebuilt.advisory_id,
            source_prompt=str(payload.get("source_prompt", "")),
            advisory_text=str(payload.get("advisory_text", "")),
            context_tags=list(payload.get("context_tags", [])),
            status=str(payload.get("status", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "subsystem": self.subsystem,
            "lane": self.lane,
            "request_id": self.request_id,
            "advisory_id": self.advisory_id,
            "source_prompt": self.source_prompt,
            "advisory_text": self.advisory_text,
            "context_tags": list(self.context_tags),
            "status": self.status,
        }
