from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from abraxas.core.canonical import canonical_json, sha256_hex

from abraxas.oracle.advisory.mircl_adapter import MirclAdapter
from abraxas.oracle.advisory.trend_adapter import TrendAdapter


@dataclass(frozen=True)
class AdvisoryRegistry:
    adapters: tuple[Any, ...]

    def invoke(self, *, authority: Mapping[str, Any], normalized: Mapping[str, Any], requested_ids: Sequence[str] | None = None) -> list[dict[str, Any]]:
        selected = set(requested_ids or [a.adapter_id for a in self.adapters])
        out: list[dict[str, Any]] = []
        authority_before = sha256_hex(canonical_json(dict(authority)))
        for adapter in sorted(self.adapters, key=lambda x: x.adapter_id):
            if adapter.adapter_id not in selected:
                continue
            attachment = dict(adapter.build(authority=deepcopy(dict(authority)), normalized=normalized))
            out.append(attachment)
            authority_after = sha256_hex(canonical_json(dict(authority)))
            if authority_after != authority_before:
                raise ValueError("advisory adapter mutated authority payload")
        return out


def default_registry() -> AdvisoryRegistry:
    return AdvisoryRegistry(adapters=(MirclAdapter(), TrendAdapter()))
