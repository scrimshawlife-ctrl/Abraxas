"""Registry for operators and other versioned components."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, Field

from abraxas.core.provenance import hash_canonical_json


class Versioned(Protocol):
    """Protocol for versioned items in registry."""

    operator_id: str
    version: str
    status: str


class RegistryEntry(BaseModel):
    """Single entry in the registry."""

    item_id: str = Field(..., description="Unique identifier")
    version: str = Field(..., description="Version string")
    status: str = Field(..., description="Status: canonical, staging, legacy, deprecated")
    data: dict[str, Any] = Field(..., description="Full item data")
    hash: str = Field(..., description="Hash of data for integrity")

    def compute_hash(self) -> str:
        """Compute hash of data field."""
        return hash_canonical_json(self.data)


class Registry(BaseModel):
    """Generic versioned registry with rollback support."""

    entries: dict[str, RegistryEntry] = Field(default_factory=dict, description="item_id -> entry")
    version_history: list[dict[str, Any]] = Field(default_factory=list, description="Rollback history")
    registry_version: int = Field(default=1, description="Registry schema version")

    def register(self, item_id: str, version: str, status: str, data: dict[str, Any]) -> None:
        """Register or update an item."""
        entry = RegistryEntry(
            item_id=item_id,
            version=version,
            status=status,
            data=data,
            hash=hash_canonical_json(data),
        )
        # Record history before update
        if item_id in self.entries:
            self.version_history.append(
                {
                    "action": "update",
                    "item_id": item_id,
                    "old_version": self.entries[item_id].version,
                    "new_version": version,
                }
            )
        else:
            self.version_history.append({"action": "add", "item_id": item_id, "version": version})

        self.entries[item_id] = entry

    def get(self, item_id: str) -> RegistryEntry | None:
        """Get entry by ID."""
        return self.entries.get(item_id)

    def list_by_status(self, status: str) -> list[RegistryEntry]:
        """List all entries with given status."""
        return [e for e in self.entries.values() if e.status == status]

    def rollback(self, steps: int = 1) -> None:
        """Rollback registry by N steps (not fully implemented - placeholder)."""
        # Full rollback would require storing complete snapshots
        # For now, just record intent
        if steps > 0:
            self.version_history.append({"action": "rollback", "steps": steps})


class OperatorRegistry:
    """Specialized registry for operators with file persistence."""

    def __init__(self, registry_path: str | Path | None = None):
        if registry_path is None:
            registry_path = Path(".aal/registry/operators.json")
        self.registry_path = Path(registry_path)
        self.registry = self._load()

    def _load(self) -> Registry:
        """Load registry from disk."""
        if self.registry_path.exists():
            with open(self.registry_path, "r") as f:
                data = json.load(f)
                return Registry(**data)
        return Registry()

    def _save(self) -> None:
        """Save registry to disk."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, "w") as f:
            json.dump(self.registry.model_dump(), f, indent=2, default=str)

    def register(self, operator_id: str, version: str, status: str, data: dict[str, Any]) -> None:
        """Register an operator."""
        self.registry.register(operator_id, version, status, data)
        self._save()

    def get(self, operator_id: str) -> RegistryEntry | None:
        """Get operator entry."""
        return self.registry.get(operator_id)

    def list_canonical(self) -> list[RegistryEntry]:
        """List all canonical operators."""
        return self.registry.list_by_status("canonical")

    def list_staging(self) -> list[RegistryEntry]:
        """List all staging operators."""
        return self.registry.list_by_status("staging")

    def rollback(self, version: str) -> None:
        """Rollback to a specific version (simplified)."""
        self.registry.rollback(steps=1)
        self._save()

    def load_operators(self) -> list[dict[str, Any]]:
        """Load all canonical operators as data dicts."""
        return [entry.data for entry in self.list_canonical()]
