from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, FrozenSet, Optional


TIERS = ("psychonaut", "academic", "enterprise")


@dataclass(frozen=True)
class UserContext:
    user_id: str
    tier: str = "psychonaut"
    permissions: FrozenSet[str] = field(default_factory=frozenset)
    feature_flags: Dict[str, bool] = field(default_factory=dict)

    def __post_init__(self):
        if self.tier not in TIERS:
            raise ValueError(f"Invalid tier: {self.tier}")

    @property
    def is_admin(self) -> bool:
        return "admin" in self.permissions


@dataclass(frozen=True)
class AdminContext:
    admin_id: str
    full_visibility: bool = True
    permissions: FrozenSet[str] = field(default_factory=lambda: frozenset({"admin"}))
    # projection, promotion, export, etc. are enforced by permission checks elsewhere

    @property
    def is_admin(self) -> bool:
        return True
