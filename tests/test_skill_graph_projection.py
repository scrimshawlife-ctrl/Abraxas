from __future__ import annotations

import copy
from aal_viz.projections.skill_graph import project_find_skills_output


def _sample_find_skills_output() -> dict:
    return {
        "status": "OK",
        "query_hash": "qh-001",
        "matches": [
            {
                "skill_id": "RUNE.FIND_SKILLS",
                "name": "Find Skills",
                "description": "Deterministic registered-skill discovery",
                "domains": ["discovery"],
                "capabilities": ["find", "registry"],
                "confidence": 0.9,
                "source": "aal_core/runes/catalog.v0.yaml",
                "provenance": {
                    "registry_path": "aal_core/runes/catalog.v0.yaml",
                    "hash": "prov-1",
                },
            },
            {
                "skill_id": "RUNE.SCAN",
                "name": "Scan",
                "description": "Scan sources",
                "domains": ["discovery"],
                "capabilities": ["scan"],
                "confidence": 0.8,
                "source": "aal_core/runes/catalog.v0.yaml",
                "provenance": {
                    "registry_path": "aal_core/runes/catalog.v0.yaml",
                    "hash": "prov-2",
                },
            },
        ],
        "total": 2,
        "shadow_summary": {
            "duplicate_skill_ids": [],
            "missing_metadata": [],
            "capability_drift_flags": [],
        },
    }


def test_same_input_same_graph() -> None:
    payload = _sample_find_skills_output()
    first = project_find_skills_output(payload)
    second = project_find_skills_output(payload)
    assert first == second


def test_projection_contains_only_source_skills() -> None:
    payload = _sample_find_skills_output()
    projected = project_find_skills_output(payload)
    projected_skills = {n["id"].split(":", 1)[1] for n in projected["nodes"] if n["type"] == "skill"}
    source_skills = {m["skill_id"] for m in payload["matches"]}
    assert projected_skills <= source_skills


def test_all_skill_nodes_have_provenance_hash() -> None:
    projected = project_find_skills_output(_sample_find_skills_output())
    skill_nodes = [n for n in projected["nodes"] if n["type"] == "skill"]
    assert skill_nodes
    assert all(node["provenance_hash"] for node in skill_nodes)


def test_projection_id_stable() -> None:
    payload = _sample_find_skills_output()
    first = project_find_skills_output(payload)
    second = project_find_skills_output(payload)
    assert first["projection_id"] == second["projection_id"]


def test_no_upstream_mutation() -> None:
    payload = _sample_find_skills_output()
    before = copy.deepcopy(payload)
    _ = project_find_skills_output(payload)
    assert payload == before


def test_missing_find_skills_output_not_computable() -> None:
    response = project_find_skills_output(None)
    assert response["status"] == "NOT_COMPUTABLE"


def test_sorting_is_stable() -> None:
    projected = project_find_skills_output(_sample_find_skills_output())
    assert projected["nodes"] == sorted(projected["nodes"], key=lambda item: (item["type"], item["id"]))
    assert projected["edges"] == sorted(
        projected["edges"],
        key=lambda item: (item["type"], item["from"], item["to"]),
    )
