"""Overlay manifest schema and state types."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Literal

OverlayState = Literal["stopped", "running", "error"]

@dataclass(frozen=True)
class OverlayManifest:
    """Overlay manifest definition."""
    name: str
    version: str
    entrypoint: str  # python import path "pkg.module:main"
    requires_gpu: bool
    min_ram_mb: int
    ports: List[int]
    description: str = ""

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "OverlayManifest":
        """Load manifest from dictionary."""
        return OverlayManifest(
            name=str(d["name"]),
            version=str(d.get("version", "0.0.0")),
            entrypoint=str(d["entrypoint"]),
            requires_gpu=bool(d.get("requires_gpu", False)),
            min_ram_mb=int(d.get("min_ram_mb", 0)),
            ports=[int(x) for x in d.get("ports", [])],
            description=str(d.get("description", "")),
        )
