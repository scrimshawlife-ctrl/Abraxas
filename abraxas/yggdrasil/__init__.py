"""
Yggdrasil — Central Decision Layer for Abraxas

This module implements Yggdrasil as the central coordinator with:
- Rune Registry (source of truth)
- Ritual Engine (drives execution pipeline)
- Topology Router (audit → hash → validate → route)
- Evidence Collector interface
- 6-gate governance integration
- Cypher persistent memory layer
"""

from .coordinator import YggdrasilCoordinator
from .registry import YggdrasilEngineRegistry
from .ritual import RitualEngine
from .memory import CypherMemoryLayer

__version__ = "1.0.0"
__all__ = [
    "YggdrasilCoordinator",
    "YggdrasilEngineRegistry",
    "RitualEngine",
    "CypherMemoryLayer",
]

# Global coordinator instance
coordinator = YggdrasilCoordinator()