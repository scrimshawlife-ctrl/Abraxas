"""Authority model for governed execution.

Authority is locked at construction time. Locked authority prevents
mutation of execution lanes and receipts.
"""
from __future__ import annotations

import hashlib
import json
from typing import Optional


class Authority:
    """Locked authority token for governed execution.

    Once constructed with locked=True, the authority cannot be mutated.
    All execution packets require a locked Authority.
    """

    LOCKED_SOURCE = "system"
    GOVERNANCE_FIRST = True

    def __init__(
        self,
        *,
        locked: bool = True,
        source: str = "system",
        scope: str = "shadow_only",
        projection_only: bool = True,
        inference_authority: bool = False,
    ) -> None:
        self._locked = locked
        self.source = source
        self.scope = scope
        self.projection_only = projection_only
        self.inference_authority = inference_authority

    def is_locked(self) -> bool:
        """Return True if this authority is locked (immutable)."""
        return self._locked

    def to_dict(self) -> dict:
        return {
            "locked": self._locked,
            "source": self.source,
            "scope": self.scope,
            "projection_only": self.projection_only,
            "inference_authority": self.inference_authority,
        }

    def authority_hash(self) -> str:
        canonical = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @classmethod
    def locked(
        cls,
        source: str = "system",
        scope: str = "shadow_only",
    ) -> "Authority":
        """Convenience factory for a locked authority."""
        return cls(
            locked=True,
            source=source,
            scope=scope,
            projection_only=True,
            inference_authority=False,
        )

    def __repr__(self) -> str:
        return f"Authority(locked={self._locked}, source={self.source!r}, scope={self.scope!r})"
