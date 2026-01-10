"""Capability-based rune invocation system.

Extends ABX-Runes with capability routing and contract enforcement.
Version: 2.0.0
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CapabilityContract(BaseModel):
    """Contract definition for a capability."""

    capability_id: str = Field(..., description="Unique capability identifier (e.g., 'oracle.v2.run')")
    rune_id: str = Field(..., description="Associated rune ID (e.g., 'ϟ_ORACLE_RUN')")
    operator_path: str = Field(..., description="Python module:function path to operator")
    version: str = Field(..., description="Semantic version")
    input_schema: Optional[str] = Field(None, description="Path to input JSON schema")
    output_schema: Optional[str] = Field(None, description="Path to output JSON schema")
    provenance_required: bool = Field(True, description="Must emit provenance envelope")
    deterministic: bool = Field(True, description="Must be deterministic")
    evidence_mode: str = Field("prediction_lane", description="prediction_lane | shadow_lane | detector_only")

    class Config:
        frozen = True


class CapabilityRegistry(BaseModel):
    """Registry of all capability contracts."""

    version: str = Field(..., description="Registry version")
    capabilities: List[CapabilityContract] = Field(default_factory=list)

    def find_capability(self, capability_id: str) -> Optional[CapabilityContract]:
        """Find capability by ID."""
        return next((c for c in self.capabilities if c.capability_id == capability_id), None)

    def find_by_rune(self, rune_id: str) -> Optional[CapabilityContract]:
        """Find capability by rune ID."""
        return next((c for c in self.capabilities if c.rune_id == rune_id), None)

    def list_by_prefix(self, prefix: str) -> List[CapabilityContract]:
        """List all capabilities with given prefix (e.g., 'oracle.')."""
        return [c for c in self.capabilities if c.capability_id.startswith(prefix)]


def load_capability_registry() -> CapabilityRegistry:
    """Load capability registry from runes/registry.json."""
    registry_path = Path(__file__).parent / "registry.json"
    with open(registry_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    capabilities_data = data.get("capabilities", [])
    return CapabilityRegistry(
        version=data.get("capability_version", data.get("version", "2.0.0")),
        capabilities=[CapabilityContract(**c) for c in capabilities_data]
    )


def register_capability(
    capability_id: str,
    rune_id: str,
    operator_path: str,
    version: str,
    **kwargs
) -> CapabilityContract:
    """Register a new capability (for testing/dynamic registration)."""
    return CapabilityContract(
        capability_id=capability_id,
        rune_id=rune_id,
        operator_path=operator_path,
        version=version,
        **kwargs
    )


__all__ = [
    "CapabilityContract",
    "CapabilityRegistry",
    "load_capability_registry",
    "register_capability",
]
