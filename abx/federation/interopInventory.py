from __future__ import annotations

from abx.federation.types import ModuleInteropRecord


def build_interop_inventory() -> list[ModuleInteropRecord]:
    rows = [
        ModuleInteropRecord("interop.boundary.runtime", "boundary", "runtime", "canonical", "contract.input.envelope.v1"),
        ModuleInteropRecord("interop.runtime.observability", "runtime", "observability", "canonical", "contract.runtime.events.v1"),
        ModuleInteropRecord("interop.resilience.operator", "resilience", "operator", "derived", "contract.recovery.status.v1"),
        ModuleInteropRecord("interop.knowledge.governance", "knowledge", "governance", "canonical", "contract.continuity.snapshot.v1"),
    ]
    return sorted(rows, key=lambda x: x.interop_id)
