"""Deterministic registered-skill discovery for RUNE.FIND_SKILLS."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import jsonschema
import yaml

DEFAULT_REGISTRY_SOURCE = "aal_core/runes/catalog.v0.yaml"
DEFAULT_INPUT_SCHEMA = "schemas/FindSkillsInput.v1.json"
DEFAULT_OUTPUT_SCHEMA = "schemas/FindSkillsOutput.v1.json"
DEFAULT_THRESHOLD = 0.30


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_text_tokens(value: str) -> List[str]:
    tokens = {token for token in value.strip().lower().split() if token}
    return sorted(tokens)


def _normalize_list(values: Iterable[str]) -> List[str]:
    return sorted({str(v).strip().lower() for v in values if str(v).strip()})


def _overlap_ratio(query_tokens: List[str], candidate_tokens: List[str]) -> float:
    if not query_tokens or not candidate_tokens:
        return 0.0
    q = set(query_tokens)
    c = set(candidate_tokens)
    return len(q & c) / float(len(q))


def _validate_schema(instance: Dict[str, Any], schema_path: Path) -> None:
    with schema_path.open("r", encoding="utf-8") as handle:
        schema = json.load(handle)
    jsonschema.Draft202012Validator(schema).validate(instance)


def _base_output(status: str, query_hash: str, shadow_summary: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": status,
        "matches": [],
        "total": 0,
        "query_hash": query_hash,
        "shadow_summary": shadow_summary,
    }


def _schema_file_exists(base_path: Path, ref: str) -> bool:
    schema_path = ref.split("#", 1)[0]
    if not schema_path:
        return False
    return (base_path / schema_path).exists()


def _extract_skill(record: Dict[str, Any], registry_path: str) -> Dict[str, Any]:
    skill_id = str(record.get("id") or record.get("rune_id") or "").strip()
    name = str(record.get("name") or "").strip()
    description = str(record.get("description") or "").strip()
    domains = list(record.get("domains") or [])
    capabilities = list(record.get("capabilities") or [])
    version = str(record.get("version") or "").strip()

    return {
        "skill_id": skill_id,
        "name": name,
        "description": description,
        "domains": [str(v) for v in domains],
        "capabilities": [str(v) for v in capabilities],
        "version": version,
        "registry_path": registry_path,
        "source": registry_path,
    }


def find_skills(
    payload: Dict[str, Any],
    *,
    base_path: Path | str = ".",
    input_schema_relpath: str = DEFAULT_INPUT_SCHEMA,
    output_schema_relpath: str = DEFAULT_OUTPUT_SCHEMA,
) -> Dict[str, Any]:
    """Discover registered skills with deterministic ranking and provenance."""

    root = Path(base_path)
    normalized_query = " ".join(_normalize_text_tokens(str(payload.get("query") or "")))
    normalized_domains = _normalize_list(payload.get("domains") or [])
    normalized_capabilities = _normalize_list(payload.get("capabilities") or [])
    sources = sorted(payload.get("sources") or [DEFAULT_REGISTRY_SOURCE])
    limit = int(payload.get("limit", 10))

    hash_material = "|".join(
        [
            normalized_query,
            ",".join(normalized_domains),
            ",".join(normalized_capabilities),
            str(limit),
            ",".join(sources),
        ]
    )
    query_hash = _sha256(hash_material)

    shadow_summary: Dict[str, Any] = {
        "duplicate_skill_ids": [],
        "missing_metadata": [],
        "capability_drift_flags": [],
        "orphaned_skill_files": [],
        "missing_schema_refs": [],
    }

    try:
        _validate_schema(payload, root / input_schema_relpath)
    except Exception:
        result = _base_output("NOT_COMPUTABLE", query_hash, shadow_summary)
        _validate_schema(result, root / output_schema_relpath)
        return result

    if not normalized_query:
        result = _base_output("NOT_COMPUTABLE", query_hash, shadow_summary)
        _validate_schema(result, root / output_schema_relpath)
        return result

    if any(source != DEFAULT_REGISTRY_SOURCE for source in sources):
        result = _base_output("NOT_COMPUTABLE", query_hash, shadow_summary)
        _validate_schema(result, root / output_schema_relpath)
        return result

    records: List[Dict[str, Any]] = []
    try:
        for source in sources:
            source_path = root / source
            if not source_path.exists():
                result = _base_output("NOT_COMPUTABLE", query_hash, shadow_summary)
                _validate_schema(result, root / output_schema_relpath)
                return result
            with source_path.open("r", encoding="utf-8") as handle:
                loaded = yaml.safe_load(handle)
            rune_records = loaded.get("runes") if isinstance(loaded, dict) else None
            if not isinstance(rune_records, list):
                result = _base_output("NOT_COMPUTABLE", query_hash, shadow_summary)
                _validate_schema(result, root / output_schema_relpath)
                return result
            for item in rune_records:
                if isinstance(item, dict):
                    records.append(_extract_skill(item, source))
    except Exception:
        result = _base_output("NOT_COMPUTABLE", query_hash, shadow_summary)
        _validate_schema(result, root / output_schema_relpath)
        return result

    skill_id_to_sources: Dict[str, List[str]] = {}
    name_to_capabilities: Dict[str, List[Tuple[str, ...]]] = {}

    for record in records:
        skill_id = record["skill_id"]
        if skill_id:
            skill_id_to_sources.setdefault(skill_id, []).append(record["registry_path"])

        missing_fields = [
            field
            for field in ("name", "description", "domains", "capabilities")
            if not record.get(field)
        ]
        if missing_fields:
            shadow_summary["missing_metadata"].append(
                {"skill_id": skill_id or "UNKNOWN", "fields": sorted(missing_fields)}
            )

        if record.get("name"):
            cap_tuple = tuple(sorted(record.get("capabilities") or []))
            name_to_capabilities.setdefault(record["name"], []).append(cap_tuple)

    for skill_id, source_list in sorted(skill_id_to_sources.items()):
        if len(source_list) > 1:
            shadow_summary["duplicate_skill_ids"].append(
                {"skill_id": skill_id, "sources": sorted(source_list)}
            )

    for name, capability_sets in sorted(name_to_capabilities.items()):
        unique_sets = sorted({tuple(v) for v in capability_sets})
        if len(unique_sets) > 1:
            shadow_summary["capability_drift_flags"].append(
                {"name": name, "capability_sets": [list(v) for v in unique_sets]}
            )

    skills_dir = root / "skills"
    if skills_dir.exists() and skills_dir.is_dir():
        registered_ids = {record["skill_id"] for record in records if record["skill_id"]}
        for file_path in sorted(skills_dir.glob("**/*")):
            if file_path.is_file():
                candidate_id = file_path.stem
                if candidate_id not in registered_ids:
                    shadow_summary["orphaned_skill_files"].append(str(file_path.relative_to(root)))

    for source in sources:
        source_path = root / source
        with source_path.open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle)
        for item in loaded.get("runes", []):
            if not isinstance(item, dict):
                continue
            for key in ("input_schema", "output_schema", "input_schema_ref", "output_schema_ref"):
                if key in item and not _schema_file_exists(root, str(item[key])):
                    shadow_summary["missing_schema_refs"].append(
                        {
                            "skill_id": str(item.get("id") or item.get("rune_id") or "UNKNOWN"),
                            "schema_ref": str(item[key]),
                        }
                    )

    query_tokens = _normalize_text_tokens(normalized_query)

    matches = []
    for record in records:
        skill_id = record["skill_id"]
        if not skill_id:
            continue

        name_tokens = _normalize_text_tokens(record["name"])
        desc_tokens = _normalize_text_tokens(record["description"])
        capability_tokens = _normalize_list(record["capabilities"])
        domain_tokens = _normalize_list(record["domains"])

        capability_query = normalized_capabilities or query_tokens
        domain_query = normalized_domains or query_tokens

        score = (
            _overlap_ratio(query_tokens, name_tokens) * 0.40
            + _overlap_ratio(capability_query, capability_tokens) * 0.30
            + _overlap_ratio(domain_query, domain_tokens) * 0.20
            + _overlap_ratio(query_tokens, desc_tokens) * 0.10
        )

        if score < DEFAULT_THRESHOLD:
            continue

        match_hash = _sha256(f"{skill_id}{record['version']}{record['registry_path']}")
        matches.append(
            {
                "skill_id": skill_id,
                "name": record["name"],
                "description": record["description"],
                "domains": record["domains"],
                "capabilities": record["capabilities"],
                "confidence": round(score, 6),
                "source": record["source"],
                "provenance": {
                    "registry_path": record["registry_path"],
                    "hash": match_hash,
                },
            }
        )

    matches = sorted(matches, key=lambda item: (-item["confidence"], item["skill_id"]))[:limit]
    result = {
        "status": "OK",
        "matches": matches,
        "total": len(matches),
        "query_hash": query_hash,
        "shadow_summary": shadow_summary,
    }

    _validate_schema(result, root / output_schema_relpath)
    return result
