"""Projection-only adapter for RUNE.FIND_SKILLS -> SkillGraph."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

import jsonschema

SKILL_GRAPH_SCHEMA_PATH = Path("schemas/SkillGraphProjection.v1.json")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _validate_projection_schema(projection: Dict[str, Any], *, base_path: Path | str = ".") -> None:
    schema_path = Path(base_path) / SKILL_GRAPH_SCHEMA_PATH
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(projection)


def project_find_skills_output(
    find_skills_output: Dict[str, Any] | None,
    *,
    base_path: Path | str = ".",
) -> Dict[str, Any]:
    """Build deterministic non-authoritative graph projection from FindSkillsOutput.v1."""

    if not isinstance(find_skills_output, dict):
        return {
            "status": "NOT_COMPUTABLE",
            "reason": "FindSkillsOutput missing or invalid.",
            "authority": "projection_only",
        }

    if find_skills_output.get("status") != "OK":
        return {
            "status": "NOT_COMPUTABLE",
            "reason": "FindSkillsOutput status is not OK.",
            "authority": "projection_only",
        }

    source_query_hash = str(find_skills_output.get("query_hash") or "").strip()
    matches = find_skills_output.get("matches")
    if not source_query_hash or not isinstance(matches, list):
        return {
            "status": "NOT_COMPUTABLE",
            "reason": "FindSkillsOutput is malformed.",
            "authority": "projection_only",
        }

    _ = copy.deepcopy(find_skills_output)

    nodes_by_id: Dict[str, Dict[str, str]] = {}
    edges: List[Dict[str, str]] = []

    for match in matches:
        if not isinstance(match, dict):
            return {
                "status": "NOT_COMPUTABLE",
                "reason": "FindSkillsOutput contains malformed match entries.",
                "authority": "projection_only",
            }

        skill_id = str(match.get("skill_id") or "").strip()
        skill_name = str(match.get("name") or "").strip()
        provenance = match.get("provenance") if isinstance(match.get("provenance"), dict) else {}
        provenance_hash = str(provenance.get("hash") or "").strip()

        if not skill_id or not provenance_hash:
            return {
                "status": "NOT_COMPUTABLE",
                "reason": "Skill match is missing required provenance fields.",
                "authority": "projection_only",
            }

        skill_node_id = f"skill:{skill_id}"
        nodes_by_id[skill_node_id] = {
            "id": skill_node_id,
            "label": skill_name or skill_id,
            "type": "skill",
            "provenance_hash": provenance_hash,
        }

        domains = match.get("domains") if isinstance(match.get("domains"), list) else []
        for domain in sorted({str(v).strip() for v in domains if str(v).strip()}):
            domain_node_id = f"domain:{domain.lower()}"
            if domain_node_id not in nodes_by_id:
                nodes_by_id[domain_node_id] = {
                    "id": domain_node_id,
                    "label": domain,
                    "type": "domain",
                    "provenance_hash": _sha256(f"{source_query_hash}|domain|{domain.lower()}"),
                }
            edges.append({"from": skill_node_id, "to": domain_node_id, "type": "HAS_DOMAIN"})

        capabilities = match.get("capabilities") if isinstance(match.get("capabilities"), list) else []
        for capability in sorted({str(v).strip() for v in capabilities if str(v).strip()}):
            capability_node_id = f"capability:{capability.lower()}"
            if capability_node_id not in nodes_by_id:
                nodes_by_id[capability_node_id] = {
                    "id": capability_node_id,
                    "label": capability,
                    "type": "capability",
                    "provenance_hash": _sha256(f"{source_query_hash}|capability|{capability.lower()}"),
                }
            edges.append({"from": skill_node_id, "to": capability_node_id, "type": "HAS_CAPABILITY"})

    nodes = sorted(nodes_by_id.values(), key=lambda item: (item["type"], item["id"]))
    edges = sorted(
        edges,
        key=lambda item: (item["type"], item["from"], item["to"]),
    )

    projection_material = {
        "source_query_hash": source_query_hash,
        "nodes": [(node["id"], node["provenance_hash"]) for node in nodes],
        "edges": [(edge["from"], edge["to"], edge["type"]) for edge in edges],
    }
    projection_id = _sha256(json.dumps(projection_material, sort_keys=True, separators=(",", ":")))

    projection = {
        "projection_id": projection_id,
        "source_query_hash": source_query_hash,
        "nodes": nodes,
        "edges": edges,
        "authority": "projection_only",
    }
    _validate_projection_schema(projection, base_path=base_path)
    return projection
