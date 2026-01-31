"""
ERS adapter types (v0 scaffold).

No scheduling logic. Pure contract shapes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


@dataclass(frozen=True)
class ERSJobSpec:
    job_id: str
    rune_id: str
    params: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ERSSubmitResult:
    accepted: bool
    reason: Optional[str] = None
    ers_job_id: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ERSStatus:
    state: str  # queued|running|completed|failed|unknown
    meta: Dict[str, Any] = field(default_factory=dict)
