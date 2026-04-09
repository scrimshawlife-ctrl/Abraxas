from __future__ import annotations

from typing import Any, Mapping

from abraxas.core.canonical import canonical_json


def canonical_input_blob(normalized: Mapping[str, Any]) -> str:
    return canonical_json(dict(normalized.get("hashable_core") or {}))


def canonical_authority_blob(output: Mapping[str, Any]) -> str:
    return canonical_json(dict(output.get("authority") or {}))


def canonical_full_blob(output: Mapping[str, Any]) -> str:
    return canonical_json(
        {
            "authority": dict(output.get("authority") or {}),
            "advisory_attachments": list(output.get("advisory_attachments") or []),
            "run_id": output.get("run_id"),
            "lane": output.get("lane"),
        }
    )
