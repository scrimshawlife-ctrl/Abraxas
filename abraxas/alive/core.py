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

    # Minimal signature: empty lists + aggregates
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

    # Minimal translated states (psychonaut safe defaults)
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
        "strain": {
            "signals": [],
            "notes": ["No strain computed in stub mode."]
        }
    }

    return result


# ═══════════════════════════════════════════════════════════════════════════
# CLI ENTRYPOINT (for testing)
# ═══════════════════════════════════════════════════════════════════════════


def main():
    """CLI entrypoint for testing alive_run()."""
    if len(sys.argv) < 2:
        print("Usage: python -m abraxas.alive.core <artifact_json> [tier]")
        print("\nExample:")
        print('  python -m abraxas.alive.core \'{"artifact_id": "test", "kind": "text", "content": "Hello world"}\' psychonaut')
        sys.exit(1)

    # Parse artifact from command line
    artifact_data = json.loads(sys.argv[1])
    tier = sys.argv[2] if len(sys.argv) > 2 else "psychonaut"

    # Run ALIVE
    result = alive_run(artifact=artifact_data, tier=tier)

    # Output result as JSON
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
