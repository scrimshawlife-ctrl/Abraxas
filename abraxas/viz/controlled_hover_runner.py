from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from abraxas.core.canonical import canonical_json
from abraxas.viz.controlled_hover_packet import build_packet


def run(interaction_policy_path: Path, policy_ledger_path: Path, provisioning_manifest_path: Path, ci_proof_path: Path, component_manifest_path: Path, out_path: Path) -> Dict[str, Any]:
    interaction_policy = json.loads(interaction_policy_path.read_text(encoding="utf-8"))
    policy_ledger = json.loads(policy_ledger_path.read_text(encoding="utf-8"))
    provisioning_manifest = json.loads(provisioning_manifest_path.read_text(encoding="utf-8"))
    ci_proof = json.loads(ci_proof_path.read_text(encoding="utf-8"))
    component_manifest = json.loads(component_manifest_path.read_text(encoding="utf-8"))
    packet = build_packet(interaction_policy, policy_ledger, provisioning_manifest, ci_proof, component_manifest)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(canonical_json(packet), encoding="utf-8")
    return packet
