from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional

ARTIFACT = "AAL-VIZ-FRONTEND-REGISTRY-PROVISIONING-001"
SCHEMA_VERSION = "AALVizFrontendProvisioningManifest.v1"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    return _sha256_bytes(path.read_bytes())


def _canonical(obj: Dict[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def build_manifest(
    frontend_root: str = "frontend/aal-viz",
    npm_ci_status: str = "not_run",
    npm_ci_reason: Optional[str] = None,
) -> Dict[str, Any]:
    root = Path(frontend_root)
    pkg = root / "package.json"
    lock = root / "package-lock.json"
    npmrc = root / ".npmrc"
    required_files = {
        "package.json": {"present": pkg.exists(), "sha256": _sha256_file(pkg)},
        "package-lock.json": {"present": lock.exists(), "sha256": _sha256_file(lock)},
        ".npmrc": {"present": npmrc.exists(), "sha256": _sha256_file(npmrc)},
    }
    dependency_lock_present = required_files["package-lock.json"]["present"]
    registry_config_present = required_files[".npmrc"]["present"]

    if npm_ci_status == "passed":
        frontend_execution = "verified"
    elif npm_ci_status == "failed_environment":
        frontend_execution = "not_computable_environment"
    elif npm_ci_status == "failed_code":
        frontend_execution = "blocked"
    else:
        frontend_execution = "not_computable_environment"

    proof_status = {
        "dependency_lock_present": dependency_lock_present,
        "registry_config_present": registry_config_present,
        "npm_ci_status": npm_ci_status,
        "npm_ci_reason": npm_ci_reason,
        "frontend_execution": frontend_execution,
    }
    registry_policy = {
        "registry": "https://registry.npmjs.org/",
        "fund": False,
        "audit": False,
        "credentials_required": False,
    }
    authority = {
        "frontend_provisioning_manifest": True,
        "frontend_dependency_install": False,
        "component_runtime_change": False,
        "interaction_runtime": False,
        "event_listener_binding": False,
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
    core: Dict[str, Any] = {
        "artifact": ARTIFACT,
        "schema_version": SCHEMA_VERSION,
        "frontend_root": frontend_root,
        "required_files": required_files,
        "registry_policy": registry_policy,
        "proof_status": proof_status,
        "authority": authority,
    }
    manifest_id = _sha256_bytes(_canonical(core).encode())
    manifest = dict(core)
    manifest["manifest_id"] = manifest_id
    manifest_hash = _sha256_bytes(_canonical(manifest).encode())
    manifest["manifest_hash"] = manifest_hash
    return manifest
