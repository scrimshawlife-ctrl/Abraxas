"""Chronos Evidence Provider — composes in-tree runes (per Chronos/SPEC, no re-impl).

Rune chain: SCAN → ALIGN → OVERLAY → PACKET.
All four runes are SHADOW-lane, INFLUENCE_POLICY=NONE.
The provider handles the speculative fence: overlay never leaks into observed.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from abraxas.evidence.contract import CandidateOutput, EvidenceEnvelope, EvidenceType
from abraxas.evidence.provider import EvidenceProvider
from abraxas.runes.operators import (
    chrono_align,
    chrono_overlay,
    chrono_packet,
    chrono_scan,
)


class ChronosEvidenceProvider(EvidenceProvider):
    """Real chronos provider that composes in-tree runes: SCAN → ALIGN → OVERLAY → PACKET."""

    @property
    def engine_name(self) -> str:
        return "chronos"

    @property
    def engine_version(self) -> str:
        return "chronos.temporal.v1"

    @property
    def supported_evidence_types(self) -> List[EvidenceType]:
        return [EvidenceType.TEMPORAL_REASONING]

    def get_model_identity(self) -> str:
        return "chronos-rune-composer"

    def produce_evidence(
        self,
        request_id: str,
        claim: str,
        context: Dict[str, Any],
        budget: Optional[Dict[str, Any]] = None,
    ) -> EvidenceEnvelope:
        del budget  # reserved

        events = context.get("events")
        source_family = context.get("source_family", ["chronos"])
        source_ids = context.get("source_ids", [request_id])

        # Speculative fence: no events at all → not_computable immediately
        if events is None:
            return EvidenceEnvelope(
                engine="chronos",
                engine_version=self.engine_version,
                model_identity=self.get_model_identity(),
                request_id=request_id,
                claim=claim,
                candidate_outputs=[],
                evidence_type=EvidenceType.TEMPORAL_REASONING,
                confidence=0.0,
                uncertainty=1.0,
                decision_margin=0.0,
                entropy=0.0,
                provenance={"not_computable": "no_events", "rune_chain": []},
            )

        try:
            # ---- Step 1: SCAN — observe cadence/recurrence/clustering ----
            scan_result = chrono_scan.apply_chrono_scan(
                events=events,
                source_family=source_family,
                source_ids=source_ids,
                window_config=context.get("window_config"),
                timestamp=context.get("timestamp"),
                run_id=context.get("run_id"),
            )

            # ---- Step 2: ALIGN — map SCAN metrics to a bounded window ----
            align_result = chrono_align.apply_chrono_align(
                observed_temporal_metrics=scan_result,
                candidate_actions=context.get("candidate_actions"),
                alignment_policy=context.get("alignment_policy"),
                timestamp=context.get("timestamp"),
                run_id=context.get("run_id"),
            )

            # ---- Step 3: OVERLAY — speculative symbolic timing annotations ----
            # Overlay is optional per SPEC: when no symbolic_inputs or
            # operator_notes, skip it and pass empty speculative to PACKET.
            symbolic_inputs = context.get("symbolic_inputs")
            operator_notes = context.get("operator_notes")
            if symbolic_inputs or operator_notes:
                overlay_result = chrono_overlay.apply_chrono_overlay(
                    symbolic_inputs=symbolic_inputs,
                    operator_notes=operator_notes,
                    temporal_context={
                        "scan": scan_result,
                        "align": align_result,
                    },
                    timestamp=context.get("timestamp"),
                    run_id=context.get("run_id"),
                )
                overlay_flags = (
                    overlay_result.get("speculative", {}).get(
                        "not_computable_flags", []
                    )
                )
            else:
                overlay_result = None
                overlay_flags = []

            # ---- Step 4: PACKET — compose TemporalAlignmentPacket.v1 ----
            # speculative fence: overlay never leaks into observed.
            # When no overlay was produced, pass None so PACKET uses
            # empty PacketSpeculative (no not_computable flags).
            packet_result = chrono_packet.apply_chrono_packet(
                observed=scan_result,
                inferred=align_result,
                speculative=overlay_result,
                provenance=scan_result.get("provenance", {}),
                timestamp=context.get("timestamp"),
                run_id=context.get("run_id"),
            )

            # ---- Extract confidence from the composed packet ----
            packet = packet_result.get("temporal_alignment_packet", {})
            is_not_computable = packet.get("status") == "not_computable"

            # Confidence primarily from observed recurrence_strength
            pkt_observed = packet.get("observed", {})
            recurrence_strength = pkt_observed.get("recurrence_strength") or 0.0
            confidence = 0.0 if is_not_computable else recurrence_strength
            uncertainty = 1.0 - confidence

            # Collect not_computable flags from each rune phase
            scan_flags = (
                scan_result.get("observed", {}).get("not_computable_flags", [])
            )
            align_flags = (
                align_result.get("inferred", {}).get("not_computable_flags", [])
            )

            answer_summary = f"packet_status={packet.get('status')}"
            if scan_flags:
                answer_summary += f"; scan_not_computable_flags={scan_flags}"

            return EvidenceEnvelope(
                engine="chronos",
                engine_version=self.engine_version,
                model_identity=self.get_model_identity(),
                request_id=request_id,
                claim=claim,
                candidate_outputs=[
                    CandidateOutput(
                        answer=answer_summary,
                        confidence=confidence,
                        reasoning_trace="SCAN→ALIGN→OVERLAY→PACKET rune chain",
                        relation_steps=[],
                    )
                ],
                evidence_type=EvidenceType.TEMPORAL_REASONING,
                confidence=confidence,
                uncertainty=uncertainty,
                decision_margin=0.0,
                entropy=0.0,
                provenance={
                    "rune_chain": ["scan", "align", "overlay", "packet"],
                    "lane": "SHADOW",
                    "not_computable": is_not_computable,
                    "scan_flags": scan_flags,
                    "align_flags": align_flags,
                    "overlay_flags": overlay_flags,
                    "packet_status": packet.get("status"),
                },
            )

        except Exception as exc:
            return EvidenceEnvelope(
                engine="chronos",
                engine_version=self.engine_version,
                model_identity=self.get_model_identity(),
                request_id=request_id,
                claim=claim,
                candidate_outputs=[],
                evidence_type=EvidenceType.TEMPORAL_REASONING,
                confidence=0.0,
                uncertainty=1.0,
                decision_margin=0.0,
                entropy=0.0,
                provenance={
                    "error": str(exc),
                    "rune_chain": ["scan", "align", "overlay", "packet"],
                    "not_computable": True,
                },
            )


def create_chronos_adapter() -> EvidenceProvider:
    return ChronosEvidenceProvider()
