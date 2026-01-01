"""
Tests for building SMV units from vector map.
"""

from abraxas.value.smv import build_units_from_vector_map


def test_smv_build_units_from_vector_map(tmp_path):
    vector_map_path = tmp_path / "vector_map.yaml"
    vector_map_path.write_text(
        """
version: "0.1.0"
created_at: "2025-12-26"
nodes:
  - node_id: "node_a"
    domain: "INTEGRITY"
    description: "Node A"
    allowlist_source_ids: ["src_a", "src_b"]
    cadence_hint: "daily"
    narrative_affinity: ["N1_primary"]
    enabled: true
  - node_id: "node_b"
    domain: "AALMANAC"
    description: "Node B"
    allowlist_source_ids: ["src_c"]
    cadence_hint: "weekly"
    narrative_affinity: ["N2_counter"]
    enabled: true
settings:
  max_nodes_active: 10
  min_allowlist_sources_per_node: 1
  max_allowlist_sources_per_node: 5
  require_domain_validation: true
  allowed_domains: ["INTEGRITY", "PROPAGANDA", "AALMANAC", "MW"]
  allowed_cadences: ["hourly", "daily", "weekly"]
""".lstrip()
    )

    units = build_units_from_vector_map(str(vector_map_path))
    unit_ids = [unit.unit_id for unit in units]

    assert unit_ids == ["node_a", "node_b", "src_a", "src_b", "src_c"]
