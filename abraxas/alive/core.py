"""
ALIVE Engine - Core computation entry point.

INTENTIONALLY DUMB at this stage. Proves plumbing before intelligence.

The core entrypoint is alive_run():
    artifact → AliveRunResult (shape-correct, placeholder math)
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import uuid
from typing import Any, Dict, List, Optional

from abraxas.alive.lens.psychonaut import psychonaut_translate
from abraxas.alive.metrics.im_ncr import compute_im_ncr
from abraxas.alive.metrics.im_rfc import compute_im_rfc
from abraxas.alive.metrics.ll_lfc import compute_ll_lfc
from abraxas.alive.metrics.vm_gi import compute_vm_gi
from abraxas.alive.strain.v0_1 import compute_strain


def _sha256(obj: Any) -> str:
    """Generate SHA-256 hash of object."""
    blob = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _get_metric_value(signature: Dict[str, Any], metric_id: str) -> float:
    """Extract metric value from signature by ID."""
    for axis in ("influence", "vitality", "life_logistics"):
        for m in signature.get(axis, []) or []:
            if m.get("metric_id") == metric_id:
                return float(m.get("value", 0.0))
    return 0.0


def alive_run(
    artifact: Dict[str, Any],
    tier: str,
    profile: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    ALIVE core entrypoint: returns a schema-correct AliveRunResult.

    INTENTIONALLY DUMB. Proves plumbing before intelligence.

    Args:
        artifact: Normalized artifact bundle (text/url/meta)
        tier: 'psychonaut' | 'academic' | 'enterprise'
        profile: Onboarding weights/traits (optional)

    Returns:
        AliveRunResult as dict (shape-correct, placeholder math)
    """
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    input_hash = _sha256(artifact)
    profile_hash = _sha256(profile) if profile else None

    run_id = str(uuid.uuid4())

    # Extract text content from artifact
    text = artifact.get("text", artifact.get("content", ""))
    if not text and "payload" in artifact:
        payload = artifact.get("payload")
        if isinstance(payload, str):
            text = payload
        else:
            try:
                text = json.dumps(payload, sort_keys=True, ensure_ascii=False)
            except TypeError:
                text = str(payload)
    if not text:
        text = artifact.get("title") or artifact.get("notes") or artifact.get("url") or ""

    # Initialize signature
    signature = {
        "influence": [],
        "vitality": [],
        "life_logistics": [],
        "aggregates": {
            "influence_intensity": {"value": 0.0, "confidence": 0.0},
            "vitality_charge": {"value": 0.0, "confidence": 0.0},
            "logistics_friction": {"value": 0.0, "confidence": 0.0},
        },
    }

    # ═══════════════════════════════════════════════════════════════════════════
    # COMPUTE METRICS (if available)
    # ═══════════════════════════════════════════════════════════════════════════

    # Influence: IM.NCR
    if text:
        ncr = compute_im_ncr(text=text)
        signature["influence"].append(ncr)
        # Note: influence_intensity aggregate will be a blend later; keep empty for now

    # Influence: IM.RFC
    if text:
        rfc = compute_im_rfc(text=text)
        signature["influence"].append(rfc)

    # Vitality: VM.GI
    if text:
        gi = compute_vm_gi(text=text)
        signature["vitality"].append(gi)
        signature["aggregates"]["vitality_charge"] = {
            "value": gi["value"],
            "confidence": gi["confidence"],
        }

    # Life-Logistics: LL.LFC
    if text:
        lfc = compute_ll_lfc(text=text, profile=profile)
        signature["life_logistics"].append(lfc)
        signature["aggregates"]["logistics_friction"] = {
            "value": lfc["value"],
            "confidence": lfc["confidence"],
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # TRANSLATE TO TIER-SPECIFIC VIEW
    # ═══════════════════════════════════════════════════════════════════════════

    # ═══════════════════════════════════════════════════════════════════════════
    # COMPUTE STRAIN (metric discovery)
    # ═══════════════════════════════════════════════════════════════════════════

    # Strain signals detect when current metrics are insufficient
    strain = compute_strain(signature=signature)

    # ═══════════════════════════════════════════════════════════════════════════
    # TRANSLATE TO TIER-SPECIFIC VIEW
    # ═══════════════════════════════════════════════════════════════════════════

    # Psychonaut felt-state translation
    translated = psychonaut_translate(signature=signature, profile=profile)

    alerts: List[Dict[str, Any]] = []
    if tier == "enterprise":
        ncr_val = _get_metric_value(signature, "IM.NCR")
        rcf_val = _get_metric_value(signature, "IM.RCF")
        rfc_val = _get_metric_value(signature, "IM.RFC")
        gi_val = _get_metric_value(signature, "VM.GI")

        if rcf_val >= 0.60 and ncr_val >= 0.60 and rfc_val <= 0.35:
            alerts.append(
                {
                    "code": "SELF_SEALING_LOOP",
                    "severity": "warning",
                    "message": "High loop + high compression + low reality friction: high capture velocity, low correctability.",
                }
            )

        if rfc_val >= 0.70 and gi_val >= 0.60:
            alerts.append(
                {
                    "code": "LEARNING_NARRATIVE",
                    "severity": "notice",
                    "message": "High testability + high generativity: supports resilient learning culture.",
                }
            )

    result = {
        "provenance": {
            "run_id": run_id,
            "created_at": now,
            "schema_version": "alive-schema@1.0.0",
            "engine_version": "alive-core@0.1.0",
            "metric_registry_hash": "unwired",
            "input_hash": input_hash,
            "profile_hash": profile_hash,
            "corpus_context": {
                "corpus_version": "meta-corpus@1.0",
                "decay_policy_hash": "unwired",
            },
        },
        "artifact": {
            "artifact_id": artifact.get("artifact_id", input_hash[:12]),
            "kind": artifact.get("kind", "text"),
            "source": artifact.get("source", "user_upload"),
            "title": artifact.get("title"),
            "url": artifact.get("url"),
            "language": artifact.get("language", "en"),
            "timestamp": artifact.get("timestamp"),
            "notes": artifact.get("notes"),
            "content": artifact.get("content"),
            "payload": artifact.get("payload"),
        },
        "signature": signature,
        "view": {
            "tier": tier,
            "translated": translated,
            "metrics": signature if tier != "psychonaut" else None,
            "explanations": [],
            "alerts": alerts,
        },
        "strain": strain,
    }

    return result


# ═══════════════════════════════════════════════════════════════════════════
# CLI ENTRYPOINT (for testing)
# ═══════════════════════════════════════════════════════════════════════════


def main():
    """CLI entrypoint for testing alive_run()."""
    if len(sys.argv) < 2:
        print("Usage: python -m abraxas.alive.core <artifact_json> [tier] [profile_json]")
        print("\nExample:")
        print('  python -m abraxas.alive.core \'{"artifact_id": "test", "kind": "text", "content": "Hello world"}\' psychonaut')
        print('  python -m abraxas.alive.core \'{"content": "urgent crisis"}\' psychonaut \'{"capacity": {"time": 0.2}}\'')
        sys.exit(1)

    # Parse artifact from command line
    artifact_data = json.loads(sys.argv[1])
    tier = sys.argv[2] if len(sys.argv) > 2 else "psychonaut"
    profile = json.loads(sys.argv[3]) if len(sys.argv) > 3 else None

    # Run ALIVE
    result = alive_run(artifact=artifact_data, tier=tier, profile=profile)

    # Output result as JSON
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
