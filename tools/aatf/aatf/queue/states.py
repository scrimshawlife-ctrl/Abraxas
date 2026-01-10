from __future__ import annotations

from enum import Enum


class QueueState(str, Enum):
    NEW = "NEW"
    READY = "READY"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPORTED = "EXPORTED"
