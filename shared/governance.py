# Governance ledger (v0.1) — append-only receipts for state-changing actions

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from shared.signing import hmac_sign, hmac_verify

DEFAULT_LEDGER_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "governance.jsonl"
)


def _stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def record_receipt(
    *,
    action_rune_id: str,
    action_payload: Dict[str, Any],
    evidence_bundle: Dict[str, Any],
    decision: str,
    decided_by: str,
    reason: Optional[str] = None,
    provenance_bundle: Optional[Dict[str, Any]] = None,
    ledger_path: Optional[str] = None,
) -> Dict[str, Any]:
    lp = ledger_path or DEFAULT_LEDGER_PATH
    os.makedirs(os.path.dirname(lp), exist_ok=True)

    ts = datetime.now(timezone.utc).isoformat()

    core = {
        "timestamp_utc": ts,
        "action_rune_id": action_rune_id,
        "action_payload_sha256": _sha256(_stable_json(action_payload)),
        "evidence_sha256": _sha256(_stable_json(evidence_bundle)),
        "decision": decision,
        "decided_by": decided_by,
    }
    receipt_id = _sha256(_stable_json(core))

    # Sign the canonical core object (cryptographic binding)
    try:
        sig_alg, key_id, signature = hmac_sign(core)
    except EnvironmentError:
        # No signing key configured - create unsigned receipt (legacy mode)
        sig_alg, key_id, signature = None, None, None

    receipt = {
        "governance_receipt_id": receipt_id,
        "timestamp_utc": ts,
        "action_rune_id": action_rune_id,
        "action_payload": action_payload,
        "evidence_bundle": evidence_bundle,
        "decision": decision,
        "decided_by": decided_by,
        "reason": reason,
        "provenance_bundle": provenance_bundle or {},
    }

    # Add signature fields if signing succeeded
    if sig_alg:
        receipt["sig_alg"] = sig_alg
        receipt["key_id"] = key_id
        receipt["signature"] = signature

    with open(lp, "a", encoding="utf-8") as file:
        file.write(_stable_json(receipt) + "\n")

    return receipt


def find_receipt(
    receipt_id: str, ledger_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    lp = ledger_path or DEFAULT_LEDGER_PATH
    if not os.path.exists(lp):
        return None
    with open(lp, "r", encoding="utf-8") as file:
        for line in file:
            try:
                receipt = json.loads(line)
            except Exception:
                continue
            if receipt.get("governance_receipt_id") == receipt_id:
                return receipt
    return None


def write_promotion_receipt(
    *,
    rune_id: str,
    registry_sha256: str,
    decision: str,
    decided_by: str,
    reason: Optional[str] = None,
    ledger_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Write a governance receipt for rune promotion (shadow→active).

    Args:
        rune_id: The rune being promoted (e.g. 'compression.detect')
        registry_sha256: SHA-256 hash of the registry snapshot
        decision: APPROVE or DENY
        decided_by: Human decision maker identifier
        reason: Optional human rationale
        ledger_path: Optional custom ledger path

    Returns:
        The governance receipt dict with governance_receipt_id
    """
    evidence_bundle = {
        "rune_id": rune_id,
        "registry_sha256": registry_sha256,
        "promotion_event": True,
    }

    return record_receipt(
        action_rune_id="governance.promote_rune",
        action_payload={"rune_id": rune_id},
        evidence_bundle=evidence_bundle,
        decision=decision,
        decided_by=decided_by,
        reason=reason,
        ledger_path=ledger_path,
    )


def find_promotion_receipt(
    rune_id: str, ledger_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Find the most recent APPROVE promotion receipt for a rune.

    Args:
        rune_id: The rune to check (e.g. 'compression.detect')
        ledger_path: Optional custom ledger path

    Returns:
        The promotion receipt if found and approved, None otherwise
    """
    lp = ledger_path or DEFAULT_LEDGER_PATH
    if not os.path.exists(lp):
        return None

    # Scan ledger in reverse (most recent first)
    receipts = []
    with open(lp, "r", encoding="utf-8") as file:
        for line in file:
            try:
                receipt = json.loads(line)
            except Exception:
                continue
            if (receipt.get("action_rune_id") == "governance.promote_rune"
                and receipt.get("action_payload", {}).get("rune_id") == rune_id
                and receipt.get("decision") == "APPROVE"):
                receipts.append(receipt)

    # Return most recent by timestamp
    if receipts:
        return max(receipts, key=lambda r: r.get("timestamp_utc", ""))
    return None


def verify_receipt_obj(receipt: Dict[str, Any]) -> bool:
    """Verify the cryptographic signature of a governance receipt.

    Args:
        receipt: The receipt object to verify

    Returns:
        True if signature is valid, False if invalid or unsigned
    """
    if not receipt:
        return False

    sig_alg = receipt.get("sig_alg")
    key_id = receipt.get("key_id")
    signature = receipt.get("signature")

    # Unsigned receipts (legacy mode) are considered invalid
    if not sig_alg or not signature:
        return False

    # Reconstruct the canonical "core" exactly as used for signing
    core = {
        "timestamp_utc": receipt.get("timestamp_utc"),
        "action_rune_id": receipt.get("action_rune_id"),
        "action_payload_sha256": _sha256(_stable_json(receipt.get("action_payload", {}))),
        "evidence_sha256": _sha256(_stable_json(receipt.get("evidence_bundle", {}))),
        "decision": receipt.get("decision"),
        "decided_by": receipt.get("decided_by"),
    }

    # Verify based on algorithm
    if sig_alg == "hmac-sha256":
        return hmac_verify(core, key_id=key_id or "", signature_hex=signature or "")

    # Future: ed25519 backend
    # if sig_alg == "ed25519":
    #     return ed25519_verify(core, key_id=key_id, signature_b64=signature)

    # Unknown algorithm
    return False
