from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from abraxas.contracts.oracle_advisory_attachment_v1 import OracleAdvisoryAttachmentV1


@dataclass(frozen=True)
class MirclAdapter:
    adapter_id: str = "mircl"

    def build(self, *, authority: Mapping[str, Any], normalized: Mapping[str, Any]) -> Mapping[str, Any]:
        observations = list(dict(normalized.get("hashable_core", {})).get("payload", {}).get("observations") or [])
        if not observations:
            return OracleAdvisoryAttachmentV1(
                attachment_id=self.adapter_id,
                status="NOT_COMPUTABLE",
                computable=False,
                payload={
                    "meaning_pressure": 0.0,
                    "narrative_instability": 0.0,
                    "perception_drift": 0.0,
                    "meaning_state_summary": "NOT_COMPUTABLE",
                    "reality_state": "NOT_COMPUTABLE",
                    "dominant_controller": "NOT_COMPUTABLE",
                    "key_constraints": ["missing_observations"],
                },
                provenance={"source": "mircl", "shadow_attached": True},
            ).to_dict()

        mean_score = sum(float(x.get("score", 0.0)) for x in observations) / float(len(observations))
        mean_conf = sum(float(x.get("confidence", 0.0)) for x in observations) / float(len(observations))
        payload = {
            "meaning_pressure": round(mean_score, 6),
            "narrative_instability": round(max(0.0, 1.0 - mean_conf), 6),
            "perception_drift": round(abs(mean_score - mean_conf), 6),
            "meaning_state_summary": "bounded_advisory_reflection",
            "reality_state": "shadow_attached",
            "dominant_controller": "oracle_interpretation_core",
            "key_constraints": [
                "no_persuasion",
                "no_execution",
                "no_optimization",
                "no_autonomous_routing",
                "no_authority_expansion",
            ],
        }
        return OracleAdvisoryAttachmentV1(
            attachment_id=self.adapter_id,
            status="AVAILABLE",
            computable=True,
            payload=payload,
            provenance={"source": "mircl", "shadow_attached": True},
        ).to_dict()
