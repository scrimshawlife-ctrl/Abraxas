from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List


@dataclass
class OracleState:
    # Deterministic state payload: no live handles, no sockets, no random calls here.
    signal_layer: Dict[str, Any] = field(default_factory=dict)
    symbolic_layer: Dict[str, Any] = field(default_factory=dict)
    metric_layer: Dict[str, Any] = field(default_factory=dict)
    runic_layer: Dict[str, Any] = field(default_factory=dict)

    overlay_outputs: Dict[str, Any] = field(default_factory=dict)

    # Admin-only buffer (never emitted unless admin projection explicitly requested)
    projection_buffer: Dict[str, Any] = field(default_factory=dict)

    governance_meta: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
