"""
Rent Manifest Loader and Validator

Loads rent manifests from YAML files and validates them against the canonical schema.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

try:
    import yaml
except ImportError:
    raise ImportError("PyYAML required for rent manifest loading. Install via: pip install pyyaml")


# Valid domain values
VALID_DOMAINS = {
    "MW",
    "AALMANAC",
    "TAU",
    "INTEGRITY",
    "TER",
    "SOD",
    "ROUTING",
    "SCHEDULER",
    "GOVERNANCE",
}

# Valid manifest kinds
VALID_KINDS = {"metric", "operator", "artifact"}

# Valid I/O expectations
VALID_IO_EXPECTATIONS = {"none", "read", "write", "read_write"}


class ManifestValidationError(Exception):
    """Raised when a manifest fails validation."""

    pass


def load_all_manifests(root_dir: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Load all rent manifests from the root directory.

    Args:
        root_dir: Root directory containing rent_manifests/ subdirectory

    Returns:
        Dictionary with keys: 'metrics', 'operators', 'artifacts'
        Each value is a list of loaded manifest dicts
    """
    manifests = {"metrics": [], "operators": [], "artifacts": []}

    manifest_root = Path(root_dir) / "data" / "rent_manifests"
    if not manifest_root.exists():
        return manifests

    # Load metrics
    metrics_dir = manifest_root / "metrics"
    if metrics_dir.exists():
        manifests["metrics"] = _load_manifests_from_dir(metrics_dir)

    # Load operators
    operators_dir = manifest_root / "operators"
    if operators_dir.exists():
        manifests["operators"] = _load_manifests_from_dir(operators_dir)

    # Load artifacts
    artifacts_dir = manifest_root / "artifacts"
    if artifacts_dir.exists():
        manifests["artifacts"] = _load_manifests_from_dir(artifacts_dir)

    return manifests


def discover_component_registry(root_dir: str) -> Dict[str, List[str]]:
    """
    Discover component modules that should be covered by rent manifests.

    This registry is derived from known component namespaces in the codebase.
    """
    repo_root = Path(root_dir)
    registry_paths = {
        "metrics": ("abraxas.metrics", repo_root / "abraxas" / "metrics"),
        "operators": ("abraxas.operators", repo_root / "abraxas" / "operators"),
        "artifacts": ("abraxas.artifacts", repo_root / "abraxas" / "artifacts"),
    }

    registry: Dict[str, List[str]] = {}
    for kind, (module_prefix, directory) in registry_paths.items():
        registry[kind] = _discover_modules_in_dir(repo_root, directory, module_prefix)

    return registry


def find_unmanifested_components(
    registry: Dict[str, List[str]],
    manifests: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, List[str]]:
    """Return registry modules that lack a matching rent manifest."""
    unmanifested: Dict[str, List[str]] = {}

    for kind, modules in registry.items():
        manifest_modules = {
            manifest.get("owner_module")
            for manifest in manifests.get(kind, [])
            if manifest.get("owner_module")
        }
        unmanifested[kind] = sorted(set(modules) - manifest_modules)

    return unmanifested


def _load_manifests_from_dir(directory: Path) -> List[Dict[str, Any]]:
    """Load all YAML manifests from a directory."""
    manifests = []
    for yaml_file in directory.glob("*.yaml"):
        try:
            with open(yaml_file, "r") as f:
                manifest = yaml.safe_load(f)
                if manifest:  # Skip empty files
                    manifest["_source_file"] = str(yaml_file)
                    manifests.append(manifest)
        except Exception as e:
            print(f"Warning: Failed to load {yaml_file}: {e}")
    return manifests


def _discover_modules_in_dir(
    repo_root: Path, directory: Path, module_prefix: str
) -> List[str]:
    if not directory.exists():
        return []

    modules = set()
    for path in directory.rglob("*.py"):
        if path.name == "__init__.py":
            continue
        if "__pycache__" in path.parts:
            continue
        module_path = ".".join(path.relative_to(repo_root).with_suffix("").parts)
        if module_path.startswith(module_prefix):
            modules.add(module_path)

    return sorted(modules)


def validate_manifest(manifest: Dict[str, Any]) -> None:
    """
    Validate a rent manifest against the canonical schema.

    Raises:
        ManifestValidationError: If validation fails

    Validation rules:
    1. All required fields present
    2. Field types correct
    3. Domain/kind values valid
    4. Cost model fields non-negative
    5. Version format valid
    6. Date format valid
    """
    # Check required common fields
    _check_required_field(manifest, "id", str)
    _check_required_field(manifest, "kind", str)
    _check_required_field(manifest, "domain", str)
    _check_required_field(manifest, "description", str)
    _check_required_field(manifest, "owner_module", str)
    _check_required_field(manifest, "version", str)
    _check_required_field(manifest, "created_at", str)

    # Validate kind
    kind = manifest["kind"]
    if kind not in VALID_KINDS:
        raise ManifestValidationError(
            f"Invalid kind '{kind}'. Must be one of: {VALID_KINDS}"
        )

    # Validate domain
    domain = manifest["domain"]
    if domain not in VALID_DOMAINS:
        raise ManifestValidationError(
            f"Invalid domain '{domain}'. Must be one of: {VALID_DOMAINS}"
        )

    # Validate version format (semantic versioning)
    if not _is_valid_semver(manifest["version"]):
        raise ManifestValidationError(
            f"Invalid version format '{manifest['version']}'. Expected semantic versioning (e.g., '0.1' or '1.0.0')"
        )

    # Validate date format
    if not _is_valid_date(manifest["created_at"]):
        raise ManifestValidationError(
            f"Invalid date format '{manifest['created_at']}'. Expected ISO 8601 (YYYY-MM-DD)"
        )

    # Check inputs/outputs (required for metrics and operators)
    if kind in ["metric", "operator"]:
        _check_required_field(manifest, "inputs", list)
        _check_required_field(manifest, "outputs", list)

    # Check cost_model
    _check_required_field(manifest, "cost_model", dict)
    _validate_cost_model(manifest["cost_model"])

    # Check rent_claim
    _check_required_field(manifest, "rent_claim", dict)
    _validate_rent_claim(manifest["rent_claim"])

    # Check proof
    _check_required_field(manifest, "proof", dict)
    _validate_proof(manifest["proof"])

    # Kind-specific validation
    if kind == "operator":
        _validate_operator_manifest(manifest)
    elif kind == "artifact":
        _validate_artifact_manifest(manifest)


def _check_required_field(manifest: Dict[str, Any], field: str, expected_type: type):
    """Check that a required field exists and has the correct type."""
    if field not in manifest:
        raise ManifestValidationError(f"Missing required field: {field}")

    if not isinstance(manifest[field], expected_type):
        raise ManifestValidationError(
            f"Field '{field}' must be of type {expected_type.__name__}, got {type(manifest[field]).__name__}"
        )


def _validate_cost_model(cost_model: Dict[str, Any]):
    """Validate cost_model section."""
    if "time_ms_expected" not in cost_model:
        raise ManifestValidationError("cost_model missing 'time_ms_expected'")
    if "memory_kb_expected" not in cost_model:
        raise ManifestValidationError("cost_model missing 'memory_kb_expected'")
    if "io_expected" not in cost_model:
        raise ManifestValidationError("cost_model missing 'io_expected'")

    # Check types and values
    if not isinstance(cost_model["time_ms_expected"], int):
        raise ManifestValidationError("time_ms_expected must be an integer")
    if not isinstance(cost_model["memory_kb_expected"], int):
        raise ManifestValidationError("memory_kb_expected must be an integer")

    if cost_model["time_ms_expected"] < 0:
        raise ManifestValidationError("time_ms_expected must be non-negative")
    if cost_model["memory_kb_expected"] < 0:
        raise ManifestValidationError("memory_kb_expected must be non-negative")

    if cost_model["io_expected"] not in VALID_IO_EXPECTATIONS:
        raise ManifestValidationError(
            f"io_expected must be one of: {VALID_IO_EXPECTATIONS}"
        )


def _validate_rent_claim(rent_claim: Dict[str, Any]):
    """Validate rent_claim section."""
    if "improves" not in rent_claim:
        raise ManifestValidationError("rent_claim missing 'improves'")
    if "measurable_by" not in rent_claim:
        raise ManifestValidationError("rent_claim missing 'measurable_by'")
    if "thresholds" not in rent_claim:
        raise ManifestValidationError("rent_claim missing 'thresholds'")

    if not isinstance(rent_claim["improves"], list):
        raise ManifestValidationError("rent_claim.improves must be a list")
    if not isinstance(rent_claim["measurable_by"], list):
        raise ManifestValidationError("rent_claim.measurable_by must be a list")
    if not isinstance(rent_claim["thresholds"], dict):
        raise ManifestValidationError("rent_claim.thresholds must be a dict")

    # Check that lists are non-empty
    if len(rent_claim["improves"]) == 0:
        raise ManifestValidationError("rent_claim.improves must not be empty")
    if len(rent_claim["measurable_by"]) == 0:
        raise ManifestValidationError("rent_claim.measurable_by must not be empty")


def _validate_proof(proof: Dict[str, Any]):
    """Validate proof section."""
    if "tests" not in proof:
        raise ManifestValidationError("proof missing 'tests'")
    if "golden_files" not in proof:
        raise ManifestValidationError("proof missing 'golden_files'")
    if "ledgers_touched" not in proof:
        raise ManifestValidationError("proof missing 'ledgers_touched'")

    if not isinstance(proof["tests"], list):
        raise ManifestValidationError("proof.tests must be a list")
    if not isinstance(proof["golden_files"], list):
        raise ManifestValidationError("proof.golden_files must be a list")
    if not isinstance(proof["ledgers_touched"], list):
        raise ManifestValidationError("proof.ledgers_touched must be a list")

    # Validate test format (pytest node IDs)
    for test in proof["tests"]:
        if not isinstance(test, str):
            raise ManifestValidationError(f"Test must be a string: {test}")
        if "::" not in test:
            raise ManifestValidationError(
                f"Test must be in pytest node ID format (path::test_name): {test}"
            )


def _validate_operator_manifest(manifest: Dict[str, Any]):
    """Validate operator-specific fields."""
    if "operator_id" in manifest and manifest["operator_id"] != manifest["id"]:
        raise ManifestValidationError(
            f"operator_id must match id field (got '{manifest['operator_id']}' vs '{manifest['id']}')"
        )

    if "ter_edges_claimed" in manifest:
        if not isinstance(manifest["ter_edges_claimed"], list):
            raise ManifestValidationError("ter_edges_claimed must be a list")

        for edge in manifest["ter_edges_claimed"]:
            if not isinstance(edge, dict):
                raise ManifestValidationError("Each TER edge must be a dict")
            if "from" not in edge or "to" not in edge:
                raise ManifestValidationError(
                    "Each TER edge must have 'from' and 'to' fields"
                )


def _validate_artifact_manifest(manifest: Dict[str, Any]):
    """Validate artifact-specific fields."""
    if "artifact_id" in manifest and manifest["artifact_id"] != manifest["id"]:
        raise ManifestValidationError(
            f"artifact_id must match id field (got '{manifest['artifact_id']}' vs '{manifest['id']}')"
        )

    _check_required_field(manifest, "output_paths", list)
    _check_required_field(manifest, "uniqueness_claim", list)

    if len(manifest["output_paths"]) == 0:
        raise ManifestValidationError("output_paths must not be empty")
    if len(manifest["uniqueness_claim"]) == 0:
        raise ManifestValidationError("uniqueness_claim must not be empty")


def _is_valid_semver(version: str) -> bool:
    """Check if version string follows semantic versioning."""
    # Simple semver check: digits separated by dots
    pattern = r"^\d+\.\d+(\.\d+)?$"
    return bool(re.match(pattern, version))


def _is_valid_date(date_str: str) -> bool:
    """Check if date string is valid ISO 8601 (YYYY-MM-DD)."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def get_manifest_summary(manifests: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Generate summary statistics for loaded manifests.

    Returns:
        Dictionary with counts and lists
    """
    return {
        "total_manifests": sum(len(v) for v in manifests.values()),
        "by_kind": {
            "metrics": len(manifests["metrics"]),
            "operators": len(manifests["operators"]),
            "artifacts": len(manifests["artifacts"]),
        },
        "ids": {
            "metrics": [m["id"] for m in manifests["metrics"]],
            "operators": [m["id"] for m in manifests["operators"]],
            "artifacts": [m["id"] for m in manifests["artifacts"]],
        },
    }
