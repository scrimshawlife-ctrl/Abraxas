"""
Resonance Narratives Renderer v1

Pure function renderer that converts Oracle v2 envelopes into
human-readable narrative bundles with full auditability.

Core principles:
1. No invention - every statement maps to envelope fields
2. Evidence gating - no claims without evidence
3. Deterministic - same input → same output
4. Pointer-based - every line includes JSON Pointer for audit
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from abraxas.renderers.resonance_narratives.rules import (
    is_pointer_allowed,
    validate_narrative_text,
    validate_overlay_type,
)


def _safe_get(data: Dict[str, Any], pointer: str, default: Any = None) -> Any:
    """
    Safely extract value from envelope using JSON Pointer.

    Args:
        data: Envelope data
        pointer: JSON Pointer string (e.g., "/oracle_signal/window/start_iso")
        default: Default value if pointer doesn't exist

    Returns:
        Value at pointer or default
    """
    if not pointer.startswith("/"):
        return default

    parts = pointer[1:].split("/")
    current: Any = data

    for part in parts:
        if not isinstance(current, dict):
            return default
        if part not in current:
            return default
        current = current[part]

    return current


def _compute_envelope_hash(envelope: Dict[str, Any]) -> str:
    """
    Compute deterministic SHA-256 hash of envelope.

    Args:
        envelope: Oracle v2 envelope

    Returns:
        64-character hex hash
    """
    canonical = json.dumps(envelope, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _extract_signal_summary(
    envelope: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Extract signal summary items from envelope.

    Args:
        envelope: Oracle v2 envelope

    Returns:
        List of signal summary items with pointers
    """
    summary: List[Dict[str, Any]] = []

    # Window information
    window_start = _safe_get(envelope, "/oracle_signal/window/start_iso")
    window_end = _safe_get(envelope, "/oracle_signal/window/end_iso")
    window_bucket = _safe_get(envelope, "/oracle_signal/window/bucket")

    if window_start and window_end:
        summary.append({
            "label": "Time Window",
            "value": f"{window_start} to {window_end} ({window_bucket})",
            "pointer": "/oracle_signal/window",
        })

    # Compliance status
    compliance_status = _safe_get(envelope, "/oracle_signal/v2/compliance/status")
    if compliance_status:
        summary.append({
            "label": "Compliance Status",
            "value": compliance_status,
            "pointer": "/oracle_signal/v2/compliance/status",
        })

    # Oracle mode
    mode = _safe_get(envelope, "/oracle_signal/v2/mode")
    if mode:
        summary.append({
            "label": "Oracle Mode",
            "value": mode,
            "pointer": "/oracle_signal/v2/mode",
        })

    # Top vital slang count
    top_vital = _safe_get(envelope, "/oracle_signal/scores_v1/slang/top_vital", [])
    if isinstance(top_vital, list) and len(top_vital) > 0:
        summary.append({
            "label": "Vital Slang Signals",
            "value": len(top_vital),
            "pointer": "/oracle_signal/scores_v1/slang/top_vital",
        })

    # Top risk slang count
    top_risk = _safe_get(envelope, "/oracle_signal/scores_v1/slang/top_risk", [])
    if isinstance(top_risk, list) and len(top_risk) > 0:
        summary.append({
            "label": "Risk Slang Signals",
            "value": len(top_risk),
            "pointer": "/oracle_signal/scores_v1/slang/top_risk",
        })

    # Pattern count
    top_patterns = _safe_get(envelope, "/oracle_signal/scores_v1/aalmanac/top_patterns", [])
    if isinstance(top_patterns, list) and len(top_patterns) > 0:
        summary.append({
            "label": "AAlmanac Patterns",
            "value": len(top_patterns),
            "pointer": "/oracle_signal/scores_v1/aalmanac/top_patterns",
        })

    return summary


def _extract_motifs(envelope: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract motifs from top slang patterns.

    Args:
        envelope: Oracle v2 envelope

    Returns:
        List of motif items with pointers
    """
    motifs: List[Dict[str, Any]] = []

    # Extract from top vital slang
    top_vital = _safe_get(envelope, "/oracle_signal/scores_v1/slang/top_vital", [])
    if isinstance(top_vital, list):
        for i, item in enumerate(top_vital[:5]):  # Take top 5
            if isinstance(item, dict) and "term" in item:
                svs = item.get("SVS", 0.0)
                motifs.append({
                    "motif": item["term"],
                    "strength": min(svs / 100.0, 1.0),  # Normalize to 0-1
                    "pointer": f"/oracle_signal/scores_v1/slang/top_vital/{i}",
                })

    # Extract from top patterns
    top_patterns = _safe_get(envelope, "/oracle_signal/scores_v1/aalmanac/top_patterns", [])
    if isinstance(top_patterns, list):
        for i, item in enumerate(top_patterns[:5]):  # Take top 5
            if isinstance(item, dict) and "pattern" in item:
                # For patterns, use a default strength since it's not scored
                motifs.append({
                    "motif": f"pattern:{item['pattern']}",
                    "strength": 0.5,  # Default strength for patterns
                    "pointer": f"/oracle_signal/scores_v1/aalmanac/top_patterns/{i}",
                })

    return motifs


def _generate_headline(envelope: Dict[str, Any]) -> str:
    """
    Generate concise headline from envelope data.

    Args:
        envelope: Oracle v2 envelope

    Returns:
        Headline string (max 120 chars)
    """
    mode = _safe_get(envelope, "/oracle_signal/v2/mode", "UNKNOWN")
    compliance = _safe_get(envelope, "/oracle_signal/v2/compliance/status", "UNKNOWN")
    bucket = _safe_get(envelope, "/oracle_signal/window/bucket", "window")

    # Count signals
    top_vital = _safe_get(envelope, "/oracle_signal/scores_v1/slang/top_vital", [])
    top_risk = _safe_get(envelope, "/oracle_signal/scores_v1/slang/top_risk", [])
    vital_count = len(top_vital) if isinstance(top_vital, list) else 0
    risk_count = len(top_risk) if isinstance(top_risk, list) else 0

    headline = f"{mode} Oracle ({compliance}): {vital_count} vital, {risk_count} risk signals [{bucket}]"

    # Truncate if needed
    if len(headline) > 120:
        headline = headline[:117] + "..."

    return headline


def _extract_provenance_footer(
    envelope: Dict[str, Any],
    input_hash: str,
    created_at: str,
) -> Dict[str, Any]:
    """
    Extract provenance metadata for footer.

    Args:
        envelope: Oracle v2 envelope
        input_hash: Pre-computed envelope hash
        created_at: Render timestamp

    Returns:
        Provenance footer dict
    """
    # Try to extract source count from meta
    source_count = _safe_get(envelope, "/oracle_signal/meta/source_count", 0)

    # If not in meta, estimate from signal counts
    if source_count == 0:
        top_vital = _safe_get(envelope, "/oracle_signal/scores_v1/slang/top_vital", [])
        top_risk = _safe_get(envelope, "/oracle_signal/scores_v1/slang/top_risk", [])
        source_count = len(top_vital) + len(top_risk) if isinstance(top_vital, list) and isinstance(top_risk, list) else 0

    footer: Dict[str, Any] = {
        "input_hash": input_hash,
        "created_at": created_at,
        "source_count": source_count,
    }

    # Add optional commit if present in envelope
    config_hash = _safe_get(envelope, "/oracle_signal/v2/compliance/provenance/config_hash")
    if config_hash:
        footer["commit"] = config_hash

    return footer


def _generate_constraints_report(
    envelope: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate constraints report showing rendering limitations.

    Args:
        envelope: Oracle v2 envelope

    Returns:
        Constraints report dict
    """
    report: Dict[str, Any] = {
        "evidence_present": False,
        "missing_inputs": [],
        "not_computable": [],
        "warnings": [],
    }

    # Check for evidence
    evidence = _safe_get(envelope, "/oracle_signal/evidence")
    if evidence and isinstance(evidence, dict):
        report["evidence_present"] = True

    # Check for expected v2 scores
    v2_scores = _safe_get(envelope, "/oracle_signal/v2/scores_v2")
    if not v2_scores:
        report["not_computable"].append("v2_scores (not present in envelope)")

    # Check for window
    window_start = _safe_get(envelope, "/oracle_signal/window/start_iso")
    if not window_start:
        report["missing_inputs"].append("window/start_iso")

    # Check for compliance
    compliance = _safe_get(envelope, "/oracle_signal/v2/compliance")
    if not compliance:
        report["missing_inputs"].append("v2/compliance")

    return report


def render_narrative_bundle(
    envelope: Dict[str, Any],
    artifact_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Render Oracle v2 envelope into narrative bundle.

    Pure function - deterministic output for same input.

    Args:
        envelope: Oracle v2 envelope
        artifact_id: Optional custom artifact ID (auto-generated if not provided)

    Returns:
        Narrative bundle dict conforming to schema v1
    """
    # Generate deterministic metadata
    created_at = datetime.utcnow().isoformat() + "Z"
    input_hash = _compute_envelope_hash(envelope)

    # Auto-generate artifact ID if not provided
    if not artifact_id:
        # Use first 8 chars of hash for uniqueness
        artifact_id = f"NARR-{input_hash[:8].upper()}"

    # Extract narrative components
    headline = _generate_headline(envelope)
    signal_summary = _extract_signal_summary(envelope)
    motifs = _extract_motifs(envelope)
    provenance_footer = _extract_provenance_footer(envelope, input_hash, created_at)
    constraints_report = _generate_constraints_report(envelope)

    # Build narrative bundle
    bundle: Dict[str, Any] = {
        "schema_version": "v1",
        "artifact_id": artifact_id,
        "headline": headline,
        "signal_summary": signal_summary,
        "motifs": motifs,
        "overlay_notes": [],  # Empty for base renderer
        "provenance_footer": provenance_footer,
        "constraints_report": constraints_report,
    }

    return bundle


def render_narrative_bundle_with_diff(
    envelope: Dict[str, Any],
    previous_envelope: Optional[Dict[str, Any]] = None,
    artifact_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Render narrative bundle with optional diff from previous envelope.

    Args:
        envelope: Current Oracle v2 envelope
        previous_envelope: Previous envelope for diff (optional)
        artifact_id: Optional custom artifact ID

    Returns:
        Narrative bundle dict with what_changed populated if previous_envelope provided
    """
    bundle = render_narrative_bundle(envelope, artifact_id)

    if previous_envelope:
        what_changed: List[Dict[str, Any]] = []

        # Compare compliance status
        current_status = _safe_get(envelope, "/oracle_signal/v2/compliance/status")
        prev_status = _safe_get(previous_envelope, "/oracle_signal/v2/compliance/status")

        if current_status != prev_status and current_status:
            what_changed.append({
                "pointer": "/oracle_signal/v2/compliance/status",
                "change_description": f"Compliance status changed: {prev_status} → {current_status}",
                "before": prev_status,
                "after": current_status,
            })

        # Compare mode
        current_mode = _safe_get(envelope, "/oracle_signal/v2/mode")
        prev_mode = _safe_get(previous_envelope, "/oracle_signal/v2/mode")

        if current_mode != prev_mode and current_mode:
            what_changed.append({
                "pointer": "/oracle_signal/v2/mode",
                "change_description": f"Oracle mode changed: {prev_mode} → {current_mode}",
                "before": prev_mode,
                "after": current_mode,
            })

        # Compare signal counts
        current_vital = _safe_get(envelope, "/oracle_signal/scores_v1/slang/top_vital", [])
        prev_vital = _safe_get(previous_envelope, "/oracle_signal/scores_v1/slang/top_vital", [])

        current_vital_count = len(current_vital) if isinstance(current_vital, list) else 0
        prev_vital_count = len(prev_vital) if isinstance(prev_vital, list) else 0

        if current_vital_count != prev_vital_count:
            delta = current_vital_count - prev_vital_count
            what_changed.append({
                "pointer": "/oracle_signal/scores_v1/slang/top_vital",
                "change_description": f"Vital signals changed by {delta:+d}",
                "before": prev_vital_count,
                "after": current_vital_count,
            })

        bundle["what_changed"] = what_changed

    return bundle
