from __future__ import annotations

import hashlib
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.viz.react_component_manifest_validator import validate_manifest

ARTIFACT = "AAL-VIZ-WEBGL-REACT-COMPONENT-001"
SCHEMA_VERSION = "AALVizReactComponentManifest.v1"
SOURCE_PATHS = [
    "frontend/aal-viz/src/types/aalVizWebGL.ts",
    "frontend/aal-viz/src/components/AALVizCanaryWebGLStaticViewer.tsx",
]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_manifest(repo_root: Path) -> Dict[str, Any]:
    source_files: List[Dict[str, str]] = []
    for rel in SOURCE_PATHS:
        p = repo_root / rel
        source_files.append({"path": rel, "sha256": _sha256_bytes(p.read_bytes())})

    source_bundle_hash = sha256_hex(canonical_json(source_files))
    component = {
        "name": "AALVizCanaryWebGLStaticViewer",
        "mode": "static_single_frame",
        "request_animation_frame": False,
        "animation_runtime": False,
        "physics_simulation": False,
        "browser_runtime_mutation": False,
    }
    authority = {
        "react_component_scaffold_generation": True,
        "static_single_frame_render": True,
        "animation_runtime": False,
        "request_animation_frame": False,
        "physics_simulation": False,
        "browser_runtime_mutation": False,
        "inference": False,
        "production_activation": False,
        "baseline_mutation": False,
        "runtime_config_write": False,
        "promotion": False,
        "execution": False,
        "scheduler": False,
    }
    lineage = {"source_bundle_hash": source_bundle_hash}
    manifest = {
        "artifact": ARTIFACT,
        "schema_version": SCHEMA_VERSION,
        "manifest_id": "",
        "source_files": source_files,
        "component": component,
        "authority": authority,
        "lineage": lineage,
        "manifest_hash": "",
    }

    manifest_id_payload = {
        "artifact": ARTIFACT,
        "schema_version": SCHEMA_VERSION,
        "source_files": source_files,
        "component": component,
        "authority": authority,
        "lineage": deepcopy(lineage),
    }
    manifest["manifest_id"] = sha256_hex(canonical_json(manifest_id_payload))
    manifest["manifest_hash"] = sha256_hex(canonical_json(manifest))
    validate_manifest(manifest)
    return manifest
