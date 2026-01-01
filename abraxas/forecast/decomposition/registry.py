"""
Forecast Decomposition Registry (FDR) Loader
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

from abraxas.forecast.decomposition.types import ComponentClaim, FDRRegistry, TopicKeyPattern
from abraxas.forecast.types import Horizon


ALLOWED_DOMAINS = {"AALMANAC", "MW", "INTEGRITY", "FORECAST", "PROPAGANDA"}
ALLOWED_HORIZONS = set(Horizon.__members__.keys())


def load_fdr(path: str | Path) -> FDRRegistry:
    """
    Load FDR registry from YAML file and validate.
    """
    path = Path(path)
    with open(path, "r") as f:
        data = yaml.safe_load(f) or {}

    validate_fdr(data)
    components = _build_components(data.get("components", []))
    index = _build_index(components)

    return FDRRegistry(
        version=data["version"],
        components=components,
        index=index,
    )


def validate_fdr(data: Dict[str, Any]) -> None:
    if data.get("version") != "0.1":
        raise ValueError("FDR version must be '0.1'")

    components = data.get("components", [])
    if not isinstance(components, list):
        raise ValueError("FDR components must be a list")

    component_ids = set()
    for component in components:
        component_id = component.get("component_id")
        if not component_id or not isinstance(component_id, str):
            raise ValueError("component_id must be a non-empty string")
        if component_id in component_ids:
            raise ValueError(f"Duplicate component_id: {component_id}")
        component_ids.add(component_id)

        _validate_list(component, "domains")
        _validate_list(component, "horizons")
        _validate_list(component, "applicable_topic_keys")
        _validate_specs(component, "trigger_specs")
        _validate_specs(component, "falsifier_specs")

        for domain in component.get("domains", []):
            if domain not in ALLOWED_DOMAINS:
                raise ValueError(f"Unknown domain: {domain}")

        for horizon in component.get("horizons", []):
            if horizon not in ALLOWED_HORIZONS:
                raise ValueError(f"Unknown horizon: {horizon}")

        for pattern in component.get("applicable_topic_keys", []):
            _validate_pattern(pattern)


def match_components(
    registry: FDRRegistry,
    topic_key: str,
    horizon: str,
    domain: str,
) -> List[ComponentClaim]:
    components = []
    for component in registry.index.get((domain, horizon), ()):
        if component.matches(topic_key, horizon, domain):
            components.append(component)
    return sorted(components, key=lambda c: c.component_id)


def _build_components(raw_components: List[Dict[str, Any]]) -> Dict[str, ComponentClaim]:
    components: Dict[str, ComponentClaim] = {}
    for component in raw_components:
        patterns = tuple(
            TopicKeyPattern(pattern=pattern)
            for pattern in component.get("applicable_topic_keys", [])
        )
        claim = ComponentClaim(
            component_id=component["component_id"],
            label=component.get("label", ""),
            description=component.get("description", ""),
            domains=list(component.get("domains", [])),
            horizons=list(component.get("horizons", [])),
            applicable_topic_keys=list(component.get("applicable_topic_keys", [])),
            trigger_specs=list(component.get("trigger_specs", [])),
            falsifier_specs=list(component.get("falsifier_specs", [])),
            scoring_key=component.get("scoring_key", ""),
            notes=component.get("notes", ""),
            applicable_topic_key_patterns=patterns,
        )
        components[claim.component_id] = claim
    return components


def _build_index(components: Dict[str, ComponentClaim]) -> Dict[Tuple[str, str], Tuple[ComponentClaim, ...]]:
    index: Dict[Tuple[str, str], List[ComponentClaim]] = {}
    for component in components.values():
        for domain in component.domains:
            for horizon in component.horizons:
                index.setdefault((domain, horizon), []).append(component)

    return {
        key: tuple(sorted(value, key=lambda c: c.component_id))
        for key, value in index.items()
    }


def _validate_list(component: Dict[str, Any], key: str) -> None:
    if not isinstance(component.get(key, []), list):
        raise ValueError(f"{key} must be a list")


def _validate_specs(component: Dict[str, Any], key: str) -> None:
    specs = component.get(key, [])
    if not isinstance(specs, list):
        raise ValueError(f"{key} must be a list")
    for spec in specs:
        if not isinstance(spec, dict):
            raise ValueError(f"{key} entries must be dicts")
        if "kind" not in spec or "params" not in spec:
            raise ValueError(f"{key} entries must include kind and params")


def _validate_pattern(pattern: str) -> None:
    if "*" in pattern and not pattern.endswith("*"):
        raise ValueError(f"Invalid topic key wildcard pattern: {pattern}")
