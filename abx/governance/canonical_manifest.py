from __future__ import annotations

import json
from pathlib import Path

from abx.governance.schema_inventory import build_schema_inventory
from abx.governance.source_of_truth import build_source_of_truth_report
from abx.governance.types import CanonicalManifestArtifact
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable

BASELINE_ID = "ABX-GOV-BASELINE-001"
BASELINE_VERSION = "v1.0.0-rc1"
FROZEN_MANIFEST_PATH = Path(__file__).resolve().parent / "frozen" / "canonical_manifest_v1.json"


def _manifest_members() -> list[dict[str, str]]:
    schemas = build_schema_inventory()
    source_report = build_source_of_truth_report()

    members: list[dict[str, str]] = []
    for row in schemas:
        member_class = "EXCLUDED"
        if row.classification == "CANONICAL":
            member_class = "AUTHORITATIVE"
        elif row.classification == "ADAPTED":
            member_class = "DERIVED"
        elif row.classification == "LEGACY":
            member_class = "LEGACY_TOLERATED"

        members.append(
            {
                "member_id": row.schema_id,
                "member_type": "schema",
                "surface": row.artifact_type,
                "classification": member_class,
            }
        )

    for domain in source_report["domains"]:
        members.append(
            {
                "member_id": f"source.{domain['domain']}",
                "member_type": "source_of_truth",
                "surface": domain["authoritative_surface"],
                "classification": "AUTHORITATIVE",
            }
        )

    members.append(
        {
            "member_id": "rune.registry",
            "member_type": "registry",
            "surface": "abx.rune_contracts + abx.rune_governance",
            "classification": "AUTHORITATIVE",
        }
    )

    return sorted(members, key=lambda x: (x["member_type"], x["member_id"]))


def build_canonical_manifest() -> CanonicalManifestArtifact:
    members = _manifest_members()
    exclusions = [
        "raw_operator_stdout",
        "ad-hoc debug scripts",
        "non-governed local experiment files",
    ]
    payload = {
        "baseline_id": BASELINE_ID,
        "baseline_version": BASELINE_VERSION,
        "members": members,
        "exclusions": sorted(exclusions),
    }
    manifest_hash = sha256_bytes(dumps_stable(payload).encode("utf-8"))
    return CanonicalManifestArtifact(
        artifact_type="CanonicalManifestArtifact.v1",
        artifact_id="canonical-manifest-abx",
        baseline_id=BASELINE_ID,
        baseline_version=BASELINE_VERSION,
        members=members,
        exclusions=sorted(exclusions),
        manifest_hash=manifest_hash,
    )


def load_frozen_manifest() -> dict[str, object]:
    if not FROZEN_MANIFEST_PATH.exists():
        return {}
    return json.loads(FROZEN_MANIFEST_PATH.read_text(encoding="utf-8"))


def manifest_diff_against_frozen() -> dict[str, object]:
    current = build_canonical_manifest().__dict__
    frozen = load_frozen_manifest()
    if not frozen:
        return {
            "baseline_id": BASELINE_ID,
            "status": "NOT_COMPUTABLE",
            "added": sorted(x["member_id"] for x in current["members"]),
            "removed": [],
            "changed": [],
            "notes": ["frozen-manifest-missing"],
        }

    current_members = {x["member_id"]: x for x in current["members"]}
    frozen_members = {x["member_id"]: x for x in frozen.get("members", [])}

    added = sorted(set(current_members) - set(frozen_members))
    removed = sorted(set(frozen_members) - set(current_members))
    changed = sorted(
        key for key in sorted(set(current_members) & set(frozen_members)) if current_members[key] != frozen_members[key]
    )

    status = "VALID" if not (added or removed or changed) else "DRIFT"
    return {
        "baseline_id": BASELINE_ID,
        "status": status,
        "added": added,
        "removed": removed,
        "changed": changed,
        "notes": [],
    }
