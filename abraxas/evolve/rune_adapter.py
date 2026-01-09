"""Rune adapter for evolution capabilities.

Thin adapter layer exposing evolve.* modules via ABX-Runes capability system.
SEED Compliant: Deterministic, provenance-tracked.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from abraxas.core.provenance import canonical_envelope, hash_canonical_json
from abraxas.evolve.ledger import append_chained_jsonl as append_chained_jsonl_core
from abraxas.evolve.non_truncation import enforce_non_truncation as enforce_non_truncation_core
from abraxas.evolve.evogate_builder import build_evogate as build_evogate_core
from abraxas.evolve.rim_builder import build_rim_from_osh_ledger as build_rim_from_osh_ledger_core
from abraxas.evolve.epp_builder import build_epp as build_epp_core


def append_ledger_deterministic(
    ledger_path: str,
    record: Dict[str, Any],
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible chained JSONL ledger appender.

    Wraps existing append_chained_jsonl with provenance envelope and validation.
    Returns the step_hash for hash chain verification.

    Args:
        ledger_path: Path to JSONL ledger file (created if doesn't exist)
        record: Record to append (will be augmented with prev_hash and step_hash)
        seed: Optional deterministic seed (unused for ledger append, kept for consistency)

    Returns:
        Dictionary with step_hash, prev_hash, provenance, and optionally not_computable
    """
    # Validate inputs
    if not ledger_path or not isinstance(ledger_path, str):
        return {
            "step_hash": None,
            "prev_hash": None,
            "not_computable": {
                "reason": "Invalid ledger_path: must be non-empty string",
                "missing_inputs": ["ledger_path"]
            },
            "provenance": None
        }

    if not record or not isinstance(record, dict):
        return {
            "step_hash": None,
            "prev_hash": None,
            "not_computable": {
                "reason": "Invalid record: must be non-empty dictionary",
                "missing_inputs": ["record"]
            },
            "provenance": None
        }

    # Get previous hash before appending (for return value)
    try:
        path = Path(ledger_path)
        if not path.exists():
            prev_hash = "genesis"
        else:
            lines = path.read_text().splitlines()
            if not lines:
                prev_hash = "genesis"
            else:
                import json
                last = json.loads(lines[-1])
                prev_hash = last.get("step_hash", "genesis")
    except Exception as e:
        return {
            "step_hash": None,
            "prev_hash": None,
            "not_computable": {
                "reason": f"Failed to read ledger: {str(e)}",
                "missing_inputs": []
            },
            "provenance": None
        }

    # Call existing append_chained_jsonl function (no changes to core logic)
    try:
        append_chained_jsonl_core(ledger_path, record)
    except Exception as e:
        # Not computable - return structured error
        return {
            "step_hash": None,
            "prev_hash": None,
            "not_computable": {
                "reason": str(e),
                "missing_inputs": []
            },
            "provenance": None
        }

    # Compute step_hash for the record we just appended
    # Replicate the logic from append_chained_jsonl
    augmented_record = dict(record)
    augmented_record["prev_hash"] = prev_hash
    step_hash = hash_canonical_json(augmented_record)

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"step_hash": step_hash, "prev_hash": prev_hash},
        config={},
        inputs={"ledger_path": ledger_path, "record": record},
        operation_id="evolve.ledger.append",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "step_hash": step_hash,
        "prev_hash": prev_hash,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"]
    }


def enforce_non_truncation_deterministic(
    artifact: Dict[str, Any],
    raw_full: Any,
    raw_full_path: Optional[str] = None,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible non-truncation policy enforcer.

    Wraps existing enforce_non_truncation with provenance envelope and validation.
    Ensures artifact preserves full raw data per NT-0 policy.

    Args:
        artifact: The artifact to augment with non-truncation policy
        raw_full: Full raw data to preserve (embedded or written to disk)
        raw_full_path: Optional path to write raw_full to disk
        seed: Optional deterministic seed (unused for policy enforcement, kept for consistency)

    Returns:
        Dictionary with artifact, provenance, and optionally not_computable
    """
    # Validate inputs
    if not artifact or not isinstance(artifact, dict):
        return {
            "artifact": None,
            "not_computable": {
                "reason": "Invalid artifact: must be non-empty dictionary",
                "missing_inputs": ["artifact"]
            },
            "provenance": None
        }

    # raw_full can be any type (dict, list, string, number, etc.)
    # so we don't validate its type, but we do need it to exist
    if raw_full is None and "raw_full" not in artifact:
        return {
            "artifact": None,
            "not_computable": {
                "reason": "Invalid raw_full: must be provided",
                "missing_inputs": ["raw_full"]
            },
            "provenance": None
        }

    # Call existing enforce_non_truncation function (no changes to core logic)
    try:
        result_artifact = enforce_non_truncation_core(
            artifact=artifact,
            raw_full=raw_full,
            raw_full_path=raw_full_path
        )
    except Exception as e:
        # Not computable - return structured error
        return {
            "artifact": None,
            "not_computable": {
                "reason": str(e),
                "missing_inputs": []
            },
            "provenance": None
        }

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"artifact": result_artifact},
        config={},
        inputs={
            "artifact": artifact,
            "raw_full": raw_full,
            "raw_full_path": raw_full_path
        },
        operation_id="evolve.policy.enforce_non_truncation",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "artifact": result_artifact,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"]
    }


def build_evogate_deterministic(
    run_id: str,
    out_reports_dir: str,
    staging_root_dir: str,
    epp_path: str,
    base_policy_path: Optional[str] = None,
    baseline_metrics_path: Optional[str] = None,
    replay_inputs_dir: Optional[str] = None,
    replay_cmd: Optional[str] = None,
    thresholds: Optional[Dict[str, Any]] = None,
    ts: Optional[str] = None,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible EvoGate builder.

    Wraps existing build_evogate with provenance envelope.
    Builds evolution gate report with staging apply and replay validation.

    Args:
        run_id: Run identifier
        out_reports_dir: Directory for output reports
        staging_root_dir: Root directory for staging files
        epp_path: Path to EPP (Evolution Proposal Pack) JSON
        base_policy_path: Optional path to base policy JSON
        baseline_metrics_path: Optional path to baseline metrics JSON
        replay_inputs_dir: Optional directory for replay inputs
        replay_cmd: Optional override for ABRAXAS_REPLAY_CMD
        thresholds: Optional thresholds dict (brier_max_delta, calibration_error_max_delta)
        ts: Optional timestamp override
        seed: Optional deterministic seed (unused for evogate, kept for consistency)

    Returns:
        Dictionary with json_path, md_path, meta, provenance, and optionally not_computable
    """
    # Call existing build_evogate function (returns tuple: json_path, md_path, meta)
    try:
        json_path, md_path, meta = build_evogate_core(
            run_id=run_id,
            out_reports_dir=out_reports_dir,
            staging_root_dir=staging_root_dir,
            epp_path=epp_path,
            base_policy_path=base_policy_path,
            baseline_metrics_path=baseline_metrics_path,
            replay_inputs_dir=replay_inputs_dir,
            replay_cmd=replay_cmd,
            thresholds=thresholds,
            ts=ts
        )
    except Exception as e:
        # Not computable - return structured error
        return {
            "json_path": None,
            "md_path": None,
            "meta": None,
            "not_computable": {
                "reason": str(e),
                "missing_inputs": []
            },
            "provenance": None
        }

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"json_path": json_path, "md_path": md_path, "meta": meta},
        config={
            "staging_root_dir": staging_root_dir,
            "out_reports_dir": out_reports_dir,
            "thresholds": thresholds
        },
        inputs={
            "run_id": run_id,
            "epp_path": epp_path,
            "base_policy_path": base_policy_path,
            "baseline_metrics_path": baseline_metrics_path,
            "replay_inputs_dir": replay_inputs_dir,
            "replay_cmd": replay_cmd,
            "ts": ts
        },
        operation_id="evolve.evogate.build",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "json_path": json_path,
        "md_path": md_path,
        "meta": meta,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"]
    }


def build_rim_from_osh_ledger_deterministic(
    run_id: str,
    out_root: str,
    osh_ledger_path: Optional[str],
    max_items: int = 200,
    ts: Optional[str] = None,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible replay input manifest builder from OSH ledger.

    Wraps existing build_rim_from_osh_ledger with provenance envelope.
    Builds replay manifest from OSH fetch artifacts ledger.

    Args:
        run_id: Run identifier
        out_root: Output root directory
        osh_ledger_path: Path to OSH ledger JSONL
        max_items: Maximum items to include (default: 200)
        ts: Optional timestamp override
        seed: Optional deterministic seed (unused for rim builder, kept for consistency)

    Returns:
        Dictionary with rim_path, manifest, provenance, and optionally not_computable
    """
    # Call existing build_rim_from_osh_ledger function (returns tuple: rim_path, manifest)
    try:
        rim_path, manifest = build_rim_from_osh_ledger_core(
            run_id=run_id,
            out_root=out_root,
            osh_ledger_path=osh_ledger_path,
            max_items=max_items,
            ts=ts
        )
    except Exception as e:
        # Not computable - return structured error
        return {
            "rim_path": None,
            "manifest": None,
            "not_computable": {
                "reason": str(e),
                "missing_inputs": []
            },
            "provenance": None
        }

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"rim_path": rim_path, "manifest": manifest},
        config={"max_items": max_items, "out_root": out_root},
        inputs={
            "run_id": run_id,
            "osh_ledger_path": osh_ledger_path,
            "ts": ts
        },
        operation_id="evolve.rim.build_from_osh_ledger",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "rim_path": rim_path,
        "manifest": manifest,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"]
    }


def build_epp_deterministic(
    run_id: str,
    out_dir: str = "out/reports",
    inputs_dir: str = "out/reports",
    osh_ledger_path: str = "out/osh_ledgers/fetch_artifacts.jsonl",
    integrity_snapshot_path: Optional[str] = None,
    dap_path: Optional[str] = None,
    mwr_path: Optional[str] = None,
    a2_path: Optional[str] = None,
    a2_phase_path: Optional[str] = None,
    audit_path: Optional[str] = None,
    ledger_path: str = "out/value_ledgers/epp_runs.jsonl",
    max_proposals: int = 25,
    ts: Optional[str] = None,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible EPP (Evolution Proposal Pack) builder.

    Wraps existing build_epp with provenance envelope.
    Builds proposal pack from SMV/CRE reports, DAP, integrity snapshots, and forecasts.

    Args:
        run_id: Run identifier
        out_dir: Output directory for reports
        inputs_dir: Input directory for reports
        osh_ledger_path: Path to OSH ledger JSONL
        integrity_snapshot_path: Optional path to integrity snapshot
        dap_path: Optional path to DAP artifact
        mwr_path: Optional path to mimetic weather artifact
        a2_path: Optional path to AAlmanac/slang terms artifact
        a2_phase_path: Optional path to A2 temporal profiles artifact
        audit_path: Optional path to forecast audit artifact
        ledger_path: Path to EPP ledger
        max_proposals: Maximum proposals to include (default: 25)
        ts: Optional timestamp override
        seed: Optional deterministic seed (unused for epp, kept for consistency)

    Returns:
        Dictionary with json_path, md_path, provenance, and optionally not_computable
    """
    # Call existing build_epp function (returns tuple: json_path, md_path)
    try:
        json_path, md_path = build_epp_core(
            run_id=run_id,
            out_dir=out_dir,
            inputs_dir=inputs_dir,
            osh_ledger_path=osh_ledger_path,
            integrity_snapshot_path=integrity_snapshot_path,
            dap_path=dap_path,
            mwr_path=mwr_path,
            a2_path=a2_path,
            a2_phase_path=a2_phase_path,
            audit_path=audit_path,
            ledger_path=ledger_path,
            max_proposals=max_proposals,
            ts=ts
        )
    except Exception as e:
        # Not computable - return structured error
        return {
            "json_path": None,
            "md_path": None,
            "not_computable": {
                "reason": str(e),
                "missing_inputs": []
            },
            "provenance": None
        }

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"json_path": json_path, "md_path": md_path},
        config={
            "out_dir": out_dir,
            "inputs_dir": inputs_dir,
            "max_proposals": max_proposals
        },
        inputs={
            "run_id": run_id,
            "osh_ledger_path": osh_ledger_path,
            "integrity_snapshot_path": integrity_snapshot_path,
            "dap_path": dap_path,
            "mwr_path": mwr_path,
            "a2_path": a2_path,
            "a2_phase_path": a2_phase_path,
            "audit_path": audit_path,
            "ledger_path": ledger_path,
            "ts": ts
        },
        operation_id="evolve.epp.build",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "json_path": json_path,
        "md_path": md_path,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"]
    }


__all__ = [
    "append_ledger_deterministic",
    "enforce_non_truncation_deterministic",
    "build_evogate_deterministic",
    "build_rim_from_osh_ledger_deterministic",
    "build_epp_deterministic"
]
