"""
Source Vector Map Loader

PURPOSE:
This module loads and validates the source vector map registry.
The registry maps semantic nodes to OSH allowlist sources.

THIS IS NOT A SCRAPER:
- Does not fetch content
- Does not bypass allowlists
- Only maps topics to existing sources
"""

from pathlib import Path
from typing import Dict, List, Optional, Set
import yaml
from pydantic import BaseModel, Field


class VectorMapNode(BaseModel):
    """A semantic node in the vector map."""

    node_id: str
    domain: str
    description: str
    allowlist_source_ids: List[str]
    cadence_hint: str
    narrative_affinity: List[str]
    enabled: bool = True


class VectorMapSettings(BaseModel):
    """Settings for the vector map."""

    max_nodes_active: int = 10
    min_allowlist_sources_per_node: int = 1
    max_allowlist_sources_per_node: int = 5
    require_domain_validation: bool = True
    allowed_domains: List[str] = Field(default_factory=lambda: ["INTEGRITY", "PROPAGANDA", "AALMANAC", "MW"])
    allowed_cadences: List[str] = Field(default_factory=lambda: ["hourly", "daily", "weekly"])


class SourceVectorMap(BaseModel):
    """The complete source vector map."""

    version: str
    created_at: str
    nodes: List[VectorMapNode]
    settings: VectorMapSettings

    def get_enabled_nodes(self) -> List[VectorMapNode]:
        """Return only enabled nodes."""
        return [node for node in self.nodes if node.enabled]

    def get_nodes_by_domain(self, domain: str) -> List[VectorMapNode]:
        """Get all enabled nodes for a specific domain."""
        return [node for node in self.get_enabled_nodes() if node.domain == domain]

    def get_all_allowlist_source_ids(self) -> Set[str]:
        """Get all unique allowlist source IDs referenced by enabled nodes."""
        source_ids = set()
        for node in self.get_enabled_nodes():
            source_ids.update(node.allowlist_source_ids)
        return source_ids


class VectorMapValidationError(Exception):
    """Raised when vector map validation fails."""
    pass


def load_vector_map(path: Path) -> SourceVectorMap:
    """
    Load source vector map from YAML file.

    Args:
        path: Path to vector map YAML file

    Returns:
        Parsed and validated SourceVectorMap

    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML is malformed
        pydantic.ValidationError: If schema validation fails
    """
    if not path.exists():
        raise FileNotFoundError(f"Vector map file not found: {path}")

    with open(path, 'r') as f:
        data = yaml.safe_load(f)

    return SourceVectorMap(**data)


def validate_vector_map(
    vector_map: SourceVectorMap,
    allowlist_spec: Optional[Dict[str, any]] = None
) -> tuple[bool, List[str]]:
    """
    Validate the vector map for consistency and allowlist compliance.

    Checks:
    1. Node IDs are unique
    2. Domains are valid
    3. Allowlist source IDs exist (if allowlist_spec provided)
    4. Settings constraints are satisfied
    5. No duplicate allowlist references within a node

    Args:
        vector_map: The vector map to validate
        allowlist_spec: Optional allowlist specification to check against
                       Expected format: {"sources": [{"source_id": "...", ...}, ...]}

    Returns:
        (is_valid, error_messages)
    """
    errors: List[str] = []

    # Check 1: Node IDs must be unique
    node_ids = [node.node_id for node in vector_map.nodes]
    duplicates = [nid for nid in node_ids if node_ids.count(nid) > 1]
    if duplicates:
        errors.append(f"Duplicate node_ids found: {set(duplicates)}")

    # Check 2: Domains must be in allowed list
    if vector_map.settings.require_domain_validation:
        allowed_domains = set(vector_map.settings.allowed_domains)
        for node in vector_map.nodes:
            if node.domain not in allowed_domains:
                errors.append(
                    f"Node {node.node_id} has invalid domain '{node.domain}'. "
                    f"Allowed: {allowed_domains}"
                )

    # Check 3: Cadences must be in allowed list
    allowed_cadences = set(vector_map.settings.allowed_cadences)
    for node in vector_map.nodes:
        if node.cadence_hint not in allowed_cadences:
            errors.append(
                f"Node {node.node_id} has invalid cadence '{node.cadence_hint}'. "
                f"Allowed: {allowed_cadences}"
            )

    # Check 4: Source count bounds
    for node in vector_map.nodes:
        source_count = len(node.allowlist_source_ids)
        if source_count < vector_map.settings.min_allowlist_sources_per_node:
            errors.append(
                f"Node {node.node_id} has too few sources ({source_count}). "
                f"Min: {vector_map.settings.min_allowlist_sources_per_node}"
            )
        if source_count > vector_map.settings.max_allowlist_sources_per_node:
            errors.append(
                f"Node {node.node_id} has too many sources ({source_count}). "
                f"Max: {vector_map.settings.max_allowlist_sources_per_node}"
            )

    # Check 5: No duplicate allowlist sources within a node
    for node in vector_map.nodes:
        source_ids = node.allowlist_source_ids
        duplicates = [sid for sid in source_ids if source_ids.count(sid) > 1]
        if duplicates:
            errors.append(
                f"Node {node.node_id} has duplicate allowlist sources: {set(duplicates)}"
            )

    # Check 6: Active node count limit
    enabled_count = len(vector_map.get_enabled_nodes())
    if enabled_count > vector_map.settings.max_nodes_active:
        errors.append(
            f"Too many enabled nodes ({enabled_count}). "
            f"Max: {vector_map.settings.max_nodes_active}"
        )

    # Check 7: Allowlist source IDs exist (if allowlist spec provided)
    if allowlist_spec is not None:
        # Extract source_ids from allowlist
        allowlist_sources = allowlist_spec.get("sources", [])
        valid_source_ids = {src.get("source_id") for src in allowlist_sources if "source_id" in src}

        # Check all referenced sources exist
        referenced_source_ids = vector_map.get_all_allowlist_source_ids()
        invalid_refs = referenced_source_ids - valid_source_ids

        if invalid_refs:
            errors.append(
                f"Vector map references allowlist sources that don't exist: {invalid_refs}"
            )

    is_valid = len(errors) == 0
    return is_valid, errors


def validate_vector_map_strict(
    vector_map: SourceVectorMap,
    allowlist_spec: Optional[Dict[str, any]] = None
) -> None:
    """
    Validate vector map and raise exception if invalid.

    Args:
        vector_map: The vector map to validate
        allowlist_spec: Optional allowlist specification

    Raises:
        VectorMapValidationError: If validation fails
    """
    is_valid, errors = validate_vector_map(vector_map, allowlist_spec)
    if not is_valid:
        raise VectorMapValidationError(
            f"Vector map validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )


def get_sources_for_domain(
    vector_map: SourceVectorMap,
    domain: str
) -> Dict[str, List[str]]:
    """
    Get mapping of node_id -> allowlist_source_ids for a domain.

    Args:
        vector_map: The vector map
        domain: Domain to filter by (e.g., "INTEGRITY", "PROPAGANDA")

    Returns:
        Dictionary mapping node_id to list of source_ids
    """
    nodes = vector_map.get_nodes_by_domain(domain)
    return {
        node.node_id: node.allowlist_source_ids
        for node in nodes
    }


def get_nodes_by_cadence(
    vector_map: SourceVectorMap,
    cadence: str
) -> List[VectorMapNode]:
    """
    Get all enabled nodes with a specific cadence hint.

    Args:
        vector_map: The vector map
        cadence: Cadence to filter by (e.g., "daily", "weekly")

    Returns:
        List of nodes with matching cadence
    """
    return [
        node for node in vector_map.get_enabled_nodes()
        if node.cadence_hint == cadence
    ]


# Example usage
if __name__ == "__main__":
    from pathlib import Path

    # Load vector map
    vm_path = Path(__file__).parent.parent.parent / "data" / "vector_maps" / "source_vector_map_v0_1.yaml"

    try:
        vm = load_vector_map(vm_path)
        print(f"✓ Loaded vector map v{vm.version}")
        print(f"  Total nodes: {len(vm.nodes)}")
        print(f"  Enabled nodes: {len(vm.get_enabled_nodes())}")

        # Validate
        is_valid, errors = validate_vector_map(vm)
        if is_valid:
            print("✓ Validation passed")
        else:
            print("✗ Validation failed:")
            for err in errors:
                print(f"  - {err}")

        # Show domains
        print("\nNodes by domain:")
        for domain in vm.settings.allowed_domains:
            nodes = vm.get_nodes_by_domain(domain)
            if nodes:
                print(f"  {domain}: {len(nodes)} nodes")
                for node in nodes:
                    print(f"    - {node.node_id} ({len(node.allowlist_source_ids)} sources)")

    except Exception as e:
        print(f"✗ Error: {e}")
