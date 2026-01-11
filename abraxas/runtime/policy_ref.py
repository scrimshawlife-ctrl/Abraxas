"""
PolicyRef — Track which policy state produced each artifact.

Every emitted artifact now contains a PolicyRef.v0 inside its provenance:
- path to policy file
- sha256 of that policy at emission time
- present/missing marker

This answers the forensic question: "Which policy state produced this file?"

Later, when something drifts, you can prove whether:
- The inputs changed
- The code changed
- The policy changed
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, Optional


def _sha256_hex(b: bytes) -> str:
    """Compute SHA-256 hex digest of bytes."""
    return hashlib.sha256(b).hexdigest()


def policy_ref_for_retention(artifacts_dir: str, portable: bool = True) -> Dict[str, Any]:
    """
    Create a PolicyRef.v0 for the retention policy.

    If policy file does not exist yet, returns an explicit missing marker.
    This ensures provenance tracks whether policy existed at artifact creation time.

    Args:
        artifacts_dir: Path to artifacts directory
        portable: If True (default), use relative path pattern for determinism.
            If False, use absolute path for debugging/verification.

    Returns:
        PolicyRef.v0 dict with:
        - schema: "PolicyRef.v0"
        - policy: "retention"
        - path_pattern: relative path pattern (if portable) or absolute path
        - sha256: hash of policy content (or None if missing)
        - present: boolean indicating if policy existed
    """
    p = Path(artifacts_dir) / "policy" / "retention.json"

    # Use relative pattern for portability/determinism
    path_value = "policy/retention.json" if portable else str(p)

    if not p.exists():
        return {
            "schema": "PolicyRef.v0",
            "policy": "retention",
            "path_pattern": path_value,
            "sha256": None,
            "present": False,
        }

    b = p.read_bytes()
    return {
        "schema": "PolicyRef.v0",
        "policy": "retention",
        "path_pattern": path_value,
        "sha256": _sha256_hex(b),
        "present": True,
    }


def policy_ref_for_file(
    policy_name: str,
    policy_path: str,
) -> Dict[str, Any]:
    """
    Create a PolicyRef.v0 for an arbitrary policy file.

    Args:
        policy_name: Name/type of the policy (e.g., "retention", "emission")
        policy_path: Path to the policy file

    Returns:
        PolicyRef.v0 dict
    """
    p = Path(policy_path)

    if not p.exists():
        return {
            "schema": "PolicyRef.v0",
            "policy": policy_name,
            "path": str(p),
            "sha256": None,
            "present": False,
        }

    b = p.read_bytes()
    return {
        "schema": "PolicyRef.v0",
        "policy": policy_name,
        "path": str(p),
        "sha256": _sha256_hex(b),
        "present": True,
    }


def verify_policy_ref(
    policy_ref: Dict[str, Any],
    artifacts_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Verify a PolicyRef against current file state.

    Args:
        policy_ref: PolicyRef.v0 dict to verify
        artifacts_dir: Base directory for resolving path_pattern (required for portable refs)

    Returns:
        Verification result dict with:
        - valid: boolean
        - reason: explanation if invalid
        - current_sha256: current hash (or None)
        - ref_sha256: hash from ref
        - drift: boolean indicating if policy changed
    """
    if policy_ref.get("schema") != "PolicyRef.v0":
        return {
            "valid": False,
            "reason": f"Invalid schema: {policy_ref.get('schema')}",
            "drift": None,
        }

    # Support both old "path" and new "path_pattern" keys
    path_pattern = policy_ref.get("path_pattern") or policy_ref.get("path")
    if not path_pattern:
        return {
            "valid": False,
            "reason": "Missing path_pattern in PolicyRef",
            "drift": None,
        }

    # Resolve path: if it's a relative pattern, combine with artifacts_dir
    if artifacts_dir and not Path(path_pattern).is_absolute():
        p = Path(artifacts_dir) / path_pattern
    else:
        p = Path(path_pattern)

    ref_sha256 = policy_ref.get("sha256")
    ref_present = policy_ref.get("present", False)

    if not p.exists():
        if ref_present:
            return {
                "valid": True,
                "reason": "Policy file was removed since artifact creation",
                "current_sha256": None,
                "ref_sha256": ref_sha256,
                "drift": True,
            }
        else:
            return {
                "valid": True,
                "reason": "Policy file still absent (as at creation time)",
                "current_sha256": None,
                "ref_sha256": ref_sha256,
                "drift": False,
            }

    current_sha256 = _sha256_hex(p.read_bytes())

    if not ref_present:
        return {
            "valid": True,
            "reason": "Policy file was created after artifact creation",
            "current_sha256": current_sha256,
            "ref_sha256": ref_sha256,
            "drift": True,
        }

    if current_sha256 == ref_sha256:
        return {
            "valid": True,
            "reason": "Policy unchanged since artifact creation",
            "current_sha256": current_sha256,
            "ref_sha256": ref_sha256,
            "drift": False,
        }
    else:
        return {
            "valid": True,
            "reason": "Policy modified since artifact creation",
            "current_sha256": current_sha256,
            "ref_sha256": ref_sha256,
            "drift": True,
        }


__all__ = [
    "policy_ref_for_retention",
    "policy_ref_for_file",
    "verify_policy_ref",
]
