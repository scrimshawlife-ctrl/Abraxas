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

# Import metric implementations
try:
    from abraxas.alive.metrics.ll_lfc import compute_ll_lfc
except ImportError:
    # Graceful fallback if metrics not available
    compute_ll_lfc = None

try:
    from abraxas.alive.metrics.im_ncr import compute_im_ncr
except ImportError:
    # Graceful fallback if metrics not available
    compute_im_ncr = None

try:
    from abraxas.alive.metrics.vm_gi import compute_vm_gi
except ImportError:
    # Graceful fallback if metrics not available
    compute_vm_gi = None

# Import lens translators
try:
    from abraxas.alive.lens.psychonaut import psychonaut_translate
except ImportError:
    # Graceful fallback if lens not available
    psychonaut_translate = None

# Import strain detection
try:
    from abraxas.alive.strain.v0_1 import compute_strain
except ImportError:
    # Graceful fallback if strain not available
    compute_strain = None

def _sha256(obj: Any) -> str:
    """Generate SHA-256 hash of object."""
    blob = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


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
    if compute_im_ncr and text:
        ncr = compute_im_ncr(text=text)
        signature["influence"].append(ncr)
        # Note: influence_intensity aggregate will be a blend later; keep empty for now

    # Vitality: VM.GI
    if compute_vm_gi and text:
        gi = compute_vm_gi(text=text)
        signature["vitality"].append(gi)
        signature["aggregates"]["vitality_charge"] = {
            "value": gi["value"],
            "confidence": gi["confidence"],
        }

    # Life-Logistics: LL.LFC
    if compute_ll_lfc and text:
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
    if compute_strain:
        strain = compute_strain(signature=signature)
    else:
        strain = {"signals": [], "notes": ["No strain computed in stub mode."]}

    # ═══════════════════════════════════════════════════════════════════════════
    # TRANSLATE TO TIER-SPECIFIC VIEW
    # ═══════════════════════════════════════════════════════════════════════════

    # Psychonaut felt-state translation
    if psychonaut_translate:
        translated = psychonaut_translate(signature=signature, profile=profile)
    else:
        # Fallback if translator not available
        translated = {
            "pressure": 0.0,
            "pull": 0.0,
            "agency_delta": 0.0,
            "drift_risk": 0.0,
            "notes": ["ALIVE stub active: pipeline validated; metrics not yet populated."]
        }

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
        },
        "signature": signature,
        "view": {
            "tier": tier,
            "translated": translated,
            "metrics": signature if tier != "psychonaut" else None,
            "explanations": [],
            "alerts": [],
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
