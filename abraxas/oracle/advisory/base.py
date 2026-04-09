from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol


class AdvisoryAdapter(Protocol):
    adapter_id: str

    def build(self, *, authority: Mapping[str, Any], normalized: Mapping[str, Any]) -> Mapping[str, Any]:
        ...


@dataclass(frozen=True)
class AdvisoryContext:
    authority: Mapping[str, Any]
    normalized: Mapping[str, Any]
