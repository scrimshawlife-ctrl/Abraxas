from __future__ import annotations

import json

from abraxas.osh.executor import compile_jobs_from_dap
from abraxas.osh.registry_loaders import expand_vector_nodes_to_urls


def test_expand_vector_nodes_to_urls_uses_vector_map_and_allowlist(tmp_path):
    vector_map_path = tmp_path / "vector_map.yaml"
    vector_map_path.write_text(
        """
        nodes:
          - node_id: node_a
            allowlist_source_ids:
              - src_a
        """.strip()
    )
    allowlist_path = tmp_path / "allowlist.json"
    allowlist_path.write_text(
        json.dumps({"sources": [{"source_id": "src_a", "url": "https://example.com/a"}]})
    )

    urls, notes = expand_vector_nodes_to_urls(
        ["node_a"],
        vector_map_path=str(vector_map_path),
        allowlist_path=str(allowlist_path),
        allowlist_map_fallback_path=None,
    )

    assert urls == [("src_a", "https://example.com/a")]
    assert notes["used"] == "vector_map+allowlist"


def test_expand_vector_nodes_to_urls_falls_back_to_allowlist_map(tmp_path):
    allowlist_map_path = tmp_path / "allowlist_map.json"
    allowlist_map_path.write_text(json.dumps({"node_a": "https://example.com/a"}))

    urls, notes = expand_vector_nodes_to_urls(
        ["node_a"],
        vector_map_path=None,
        allowlist_path=None,
        allowlist_map_fallback_path=str(allowlist_map_path),
    )

    assert urls == [("node_a", "https://example.com/a")]
    assert notes["used"] == "allowlist_url_map_fallback"


def test_compile_jobs_from_dap_resolves_vector_nodes(tmp_path):
    dap_path = tmp_path / "dap.json"
    dap_path.write_text(
        json.dumps(
            {
                "plan_id": "p1",
                "actions": [
                    {
                        "action_id": "a1",
                        "kind": "ONLINE_FETCH",
                        "selector": {"vector_node_ids": ["node_a"]},
                    }
                ],
            }
        )
    )

    vector_map_path = tmp_path / "vector_map.yaml"
    vector_map_path.write_text(
        """
        nodes:
          - node_id: node_a
            allowlist_source_ids:
              - src_a
        """.strip()
    )

    allowlist_path = tmp_path / "allowlist.json"
    allowlist_path.write_text(
        json.dumps({"sources": [{"source_id": "src_a", "url": "https://example.com/a"}]})
    )

    jobs = compile_jobs_from_dap(
        dap_json_path=str(dap_path),
        run_id="run1",
        allowlist_spec_path=str(allowlist_path),
        vector_map_path=str(vector_map_path),
    )

    assert len(jobs) == 1
    job = jobs[0]
    assert job.allowlist_source_id == "src_a"
    assert job.url == "https://example.com/a"
    assert job.vector_node_id == "node_a"
