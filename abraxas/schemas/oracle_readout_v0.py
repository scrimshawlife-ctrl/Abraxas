from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class OracleReadoutV0:
    schema: str
    header: Dict[str, Any]
    vector_mix: Dict[str, Any]
    kairos: Dict[str, Any]
    runic_weather: Dict[str, Any]
    gate_and_trial: List[str]
    memetic_futurecast: Dict[str, Any]
    financials: Dict[str, Any]
    overlays: Dict[str, Any]
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": self.schema,
            "header": dict(self.header),
            "vector_mix": dict(self.vector_mix),
            "kairos": dict(self.kairos),
            "runic_weather": dict(self.runic_weather),
            "gate_and_trial": list(self.gate_and_trial),
            "memetic_futurecast": dict(self.memetic_futurecast),
            "financials": dict(self.financials),
            "overlays": dict(self.overlays),
            "provenance": dict(self.provenance),
        }
