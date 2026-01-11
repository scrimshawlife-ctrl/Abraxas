from __future__ import annotations
from typing import Dict, Any, List
from .base import AbraxasOverlay, OverlayMeta
from ..core.state import OracleState
from ..core.context import UserContext


class AALmanacOverlay(AbraxasOverlay):
    meta = OverlayMeta(
        name="aalmanac",
        version="v0.1.0",
        required_signals=("motifs",),
        output_schema="schemas/aalmanac_entry.v0.json",
    )

    def run(self, oracle_state: OracleState, user: UserContext) -> Dict[str, Any]:
        # Deterministic placeholder: output "single" + "compound" slots distinctly.
        motifs = oracle_state.symbolic_layer.get("motifs", []) or []
        entries = []

        for raw in motifs[:10]:
            s = str(raw).strip()
            if " " in s:
                typ = "compound"
                term = s
            else:
                typ = "single"
                term = s

            # Adaptation rule: allow context-shifted existing terms
            entries.append({
                "term": term,
                "type": typ,
                "origin_context": "unknown",
                "current_context": "oracle_motif_surface",
                "drift_score": 0.5,
                "velocity": 0.4,
                "half_life": "7d",
                "tier_visibility": user.tier,
            })

        return {
            "entries": entries,
            "note": "AALmanac is a ledger; promotion/curation is admin-governed.",
        }
