from __future__ import annotations
from typing import Dict, Any
from ..core.state import OracleState


def apply_admin_projection(state: OracleState) -> Dict[str, Any]:
    """
    Admin-only projection adapter.
    Produces marketing/export formats, Substack, email batches, etc.
    This never feeds back into inference.
    """
    return {
        "substack_format_ready": False,
        "export_targets": [],
        "notes": "Projection adapter is intentionally isolated.",
        "full_state_hashes": {
            "signal": "redacted_in_projection_stub",
            "symbolic": "redacted_in_projection_stub",
            "metrics": "redacted_in_projection_stub",
        },
    }
