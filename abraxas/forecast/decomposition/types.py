"""
Forecast Decomposition Registry (FDR) Types
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass(frozen=True)
class TopicKeyPattern:
    pattern: str

    def matches(self, topic_key: str) -> bool:
        if self.pattern.endswith("*"):
            prefix = self.pattern[:-1]
            return topic_key.startswith(prefix)
        return topic_key == self.pattern


@dataclass(frozen=True)
class ComponentClaim:
    component_id: str
    label: str
    description: str
    domains: List[str]
    horizons: List[str]
    applicable_topic_keys: List[str]
    trigger_specs: List[Dict[str, Any]]
    falsifier_specs: List[Dict[str, Any]]
    scoring_key: str
    notes: str
    applicable_topic_key_patterns: Tuple[TopicKeyPattern, ...] = field(
        default_factory=tuple
    )

    def matches(self, topic_key: str, horizon: str, domain: str) -> bool:
        if horizon not in self.horizons or domain not in self.domains:
            return False
        return any(pattern.matches(topic_key) for pattern in self.applicable_topic_key_patterns)


@dataclass(frozen=True)
class FDRRegistry:
    version: str
    components: Dict[str, ComponentClaim]
    index: Dict[Tuple[str, str], Tuple[ComponentClaim, ...]]
