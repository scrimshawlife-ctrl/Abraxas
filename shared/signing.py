"""Receipt signing (v0.1) — default HMAC-SHA256 (no deps). Optional Ed25519 later.

Provides cryptographic binding for governance receipts.
Default backend: HMAC-SHA256 using ABX_GOV_HMAC_KEY environment variable.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from typing import Any
import base64


def _stable_json_bytes(obj: Any) -> bytes:
    """
    Must match governance.py stable JSON choices to avoid signature drift.
    Uses same serialization as governance record_receipt.
    """
    s = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return s.encode("utf-8")


def hmac_sign(payload_obj: dict[str, Any]) -> tuple[str, str, str]:
    """Sign a payload object using HMAC-SHA256.

    Args:
        payload_obj: The canonical payload to sign (typically the "core" fields)

    Returns:
        Tuple of (sig_alg, key_id, signature_hex)
        - sig_alg: Always "hmac-sha256"
        - key_id: First 16 chars of SHA256(key) - doesn't reveal key
        - signature_hex: HMAC-SHA256 signature as hex string

    Raises:
        EnvironmentError: If ABX_GOV_HMAC_KEY is not set
    """
    key = os.environ.get("ABX_GOV_HMAC_KEY", "")
    if not key:
        raise EnvironmentError(
            "Missing ABX_GOV_HMAC_KEY for governance receipt signing (HMAC backend). "
            "Set environment variable: export ABX_GOV_HMAC_KEY='<random-secret>'"
        )

    key_bytes = key.encode("utf-8")
    key_id = hashlib.sha256(key_bytes).hexdigest()[:16]
    msg = _stable_json_bytes(payload_obj)
    sig = hmac.new(key_bytes, msg, hashlib.sha256).hexdigest()

    return ("hmac-sha256", key_id, sig)


def hmac_verify(
    payload_obj: dict[str, Any], key_id: str, signature_hex: str
) -> bool:
    """Verify an HMAC-SHA256 signature.

    Args:
        payload_obj: The canonical payload that was signed
        key_id: The key ID from the signature
        signature_hex: The signature to verify

    Returns:
        True if signature is valid, False otherwise
    """
    key = os.environ.get("ABX_GOV_HMAC_KEY", "")
    if not key:
        return False

    key_bytes = key.encode("utf-8")
    expected_key_id = hashlib.sha256(key_bytes).hexdigest()[:16]

    # Check key_id matches (prevents using wrong key)
    if expected_key_id != (key_id or ""):
        return False

    msg = _stable_json_bytes(payload_obj)
    expected_sig = hmac.new(key_bytes, msg, hashlib.sha256).hexdigest()

    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(expected_sig, signature_hex or "")


# ---- Optional Ed25519 hooks (not active unless you wire deps) ----


def ed25519_sign(payload_obj: dict[str, Any]) -> tuple[str, str, str]:
    """Sign a payload object using Ed25519.

    Requires ABX_GOV_ED25519_PRIVATE_KEY to be set as base64-encoded raw 32-byte key.
    Returns (sig_alg, key_id, signature_b64).
    """
    key_b64 = os.environ.get("ABX_GOV_ED25519_PRIVATE_KEY", "")
    if not key_b64:
        raise EnvironmentError(
            "Missing ABX_GOV_ED25519_PRIVATE_KEY for governance receipt signing (Ed25519 backend). "
            "Set environment variable with base64-encoded raw private key bytes."
        )

    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

    private_key_bytes = base64.b64decode(key_b64)
    private_key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
    public_key_bytes = private_key.public_key().public_bytes(
        encoding=Encoding.Raw, format=PublicFormat.Raw
    )
    key_id = hashlib.sha256(public_key_bytes).hexdigest()[:16]
    msg = _stable_json_bytes(payload_obj)
    signature = private_key.sign(msg)
    signature_b64 = base64.b64encode(signature).decode("utf-8")

    return ("ed25519", key_id, signature_b64)


def ed25519_verify(payload_obj: dict[str, Any], key_id: str, signature_b64: str) -> bool:
    """Verify an Ed25519 signature using ABX_GOV_ED25519_PUBLIC_KEY."""
    key_b64 = os.environ.get("ABX_GOV_ED25519_PUBLIC_KEY", "")
    if not key_b64:
        return False

    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    public_key_bytes = base64.b64decode(key_b64)
    public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
    expected_key_id = hashlib.sha256(public_key_bytes).hexdigest()[:16]
    if expected_key_id != (key_id or ""):
        return False

    msg = _stable_json_bytes(payload_obj)
    signature = base64.b64decode(signature_b64 or "")

    try:
        public_key.verify(signature, msg)
        return True
    except InvalidSignature:
        return False
