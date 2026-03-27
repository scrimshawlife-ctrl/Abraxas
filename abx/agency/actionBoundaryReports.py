from __future__ import annotations

from abx.agency.actionBoundaryInventory import build_action_boundary_inventory
from abx.agency.actionBoundaryRecords import build_side_effect_records
from abx.agency.hiddenChannelDetection import build_hidden_channel_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_action_boundary_report() -> dict[str, object]:
    boundaries = build_action_boundary_inventory()
    side_effects = build_side_effect_records()
    hidden = build_hidden_channel_records()
    report = {
        "artifactType": "ActionBoundaryAudit.v1",
        "artifactId": "action-boundary-audit",
        "boundaries": [x.__dict__ for x in boundaries],
        "sideEffects": [x.__dict__ for x in side_effects],
        "hiddenChannels": [x.__dict__ for x in hidden],
        "classification": {
            "no_side_effects": sorted(x.boundary_id for x in boundaries if x.governance_state == "NO_SIDE_EFFECTS"),
            "side_effect_observed": sorted(x.boundary_id for x in boundaries if x.governance_state == "SIDE_EFFECT_OBSERVED"),
            "side_effect_blocked": sorted(x.boundary_id for x in boundaries if x.governance_state == "SIDE_EFFECT_BLOCKED"),
            "hidden_channel_suspected": sorted(x.channel_id for x in hidden if x.risk_class == "HIDDEN_CHANNEL_SUSPECTED"),
            "hidden_channel_confirmed": sorted(x.channel_id for x in hidden if x.risk_class == "HIDDEN_CHANNEL_CONFIRMED"),
        },
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
