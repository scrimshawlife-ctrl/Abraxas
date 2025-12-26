from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


def _load_yaml_if_available(path: str) -> Optional[Dict[str, Any]]:
    if not path or not os.path.exists(path):
        return None
    try:
        import yaml  # type: ignore
    except Exception:
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else None


def _load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"JSON registry must be a mapping: {path}")
    return data


@dataclass(frozen=True)
class VectorMap:
    node_to_sources: Dict[str, List[str]]


@dataclass(frozen=True)
class Allowlist:
    source_to_url: Dict[str, str]


def load_vector_map(path: str) -> VectorMap:
    data = _load_yaml_if_available(path) or _load_json(path)
    nodes = data.get("nodes", [])
    if not isinstance(nodes, list):
        raise ValueError("vector_map.nodes must be a list")
    node_to_sources: Dict[str, List[str]] = {}
    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_id = node.get("node_id")
        source_ids = node.get("allowlist_source_ids", [])
        if isinstance(node_id, str) and isinstance(source_ids, list):
            node_to_sources[node_id] = [str(sid) for sid in source_ids if sid is not None]
    return VectorMap(node_to_sources=node_to_sources)


def load_allowlist(path: str) -> Allowlist:
    data = _load_yaml_if_available(path) or _load_json(path)
    sources = data.get("sources", [])
    if not isinstance(sources, list):
        raise ValueError("allowlist.sources must be a list")
    source_to_url: Dict[str, str] = {}
    for source in sources:
        if not isinstance(source, dict):
            continue
        sid = source.get("source_id")
        url = source.get("url")
        if isinstance(sid, str) and isinstance(url, str) and url:
            source_to_url[sid] = url
    return Allowlist(source_to_url=source_to_url)


def load_allowlist_url_map_fallback(path: Optional[str]) -> Dict[str, str]:
    if not path or not os.path.exists(path):
        return {}
    data = _load_json(path)
    out: Dict[str, str] = {}
    for key, value in data.items():
        if isinstance(key, str) and isinstance(value, str) and value:
            out[key] = value
    return out


def build_allowlist_url_map(
    allowlist_path: Optional[str],
    allowlist_map_fallback_path: Optional[str],
) -> Tuple[Dict[str, str], Dict[str, Any]]:
    notes: Dict[str, Any] = {"used": None}

    allowlist = None
    if allowlist_path:
        try:
            allowlist = load_allowlist(allowlist_path)
        except Exception as exc:
            notes["allowlist_load_error"] = f"{type(exc).__name__}: {exc}"
            allowlist = None

    if allowlist:
        notes["used"] = "allowlist_spec"
        return allowlist.source_to_url, notes

    fallback = load_allowlist_url_map_fallback(allowlist_map_fallback_path)
    notes["used"] = "allowlist_url_map_fallback" if fallback else "empty"
    return fallback, notes


def expand_vector_nodes_to_urls(
    vector_node_ids: List[str],
    vector_map_path: Optional[str],
    allowlist_path: Optional[str],
    allowlist_map_fallback_path: Optional[str],
) -> Tuple[List[Tuple[str, str]], Dict[str, Any]]:
    notes: Dict[str, Any] = {"used": None, "missing_nodes": [], "missing_sources": []}
    urls: List[Tuple[str, str]] = []

    vector_map = None
    if vector_map_path:
        try:
            vector_map = load_vector_map(vector_map_path)
        except Exception as exc:
            notes["vector_map_load_error"] = f"{type(exc).__name__}: {exc}"
            vector_map = None

    allowlist_url_map, allowlist_notes = build_allowlist_url_map(
        allowlist_path, allowlist_map_fallback_path
    )
    notes["allowlist"] = allowlist_notes

    if vector_map and allowlist_url_map:
        notes["used"] = "vector_map+allowlist"
        for node_id in vector_node_ids:
            source_ids = vector_map.node_to_sources.get(node_id)
            if not source_ids:
                notes["missing_nodes"].append(node_id)
                continue
            for source_id in source_ids:
                url = allowlist_url_map.get(source_id)
                if not url:
                    notes["missing_sources"].append(source_id)
                    continue
                urls.append((source_id, url))
        return sorted(set(urls)), notes

    notes["used"] = "allowlist_url_map_fallback"
    for node_id in vector_node_ids:
        url = allowlist_url_map.get(node_id)
        if url:
            urls.append((node_id, url))
        else:
            notes["missing_nodes"].append(node_id)
    return sorted(set(urls)), notes
