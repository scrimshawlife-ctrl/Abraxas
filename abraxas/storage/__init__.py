"""Storage package exports with lazy loading for event utilities."""

from __future__ import annotations

from .cas import CASIndexEntry, CASRef, CASStore

__all__ = ["write_events_jsonl", "read_events_jsonl", "CASIndexEntry", "CASRef", "CASStore"]


def __getattr__(name: str):
    if name in {"write_events_jsonl", "read_events_jsonl"}:
        from .events import read_events_jsonl, write_events_jsonl

        return {"write_events_jsonl": write_events_jsonl, "read_events_jsonl": read_events_jsonl}[name]
    raise AttributeError(f"module 'abraxas.storage' has no attribute {name}")
