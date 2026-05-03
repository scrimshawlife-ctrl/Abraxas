from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json


MUTATION_LEDGER_PATH = Path("out/registry/self_build_mutation_ledger.latest.json")
ROLLBACK_LEDGER_PATH = Path("out/registry/self_build_rollback_ledger.latest.json")


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _load_json(path: Path, fallback: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return fallback
    with path.open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    if not isinstance(loaded, dict):
        return fallback
    return loaded


def _validation_score(post_validation: dict[str, Any]) -> int:
    score = 0
    if post_validation.get("validator") == "PASS":
        score += 1
    operator_value = post_validation.get("operator_health", post_validation.get("operator_card"))
    if operator_value == "GREEN":
        score += 1
    if bool(post_validation.get("invariance")):
        score += 1
    return score


def run_self_build_scoring() -> dict[str, Any]:
    mutation_ledger = _load_json(
        MUTATION_LEDGER_PATH,
        {"schema_version": "SelfBuildMutationLedgerCollection.v1", "entry_count": 0, "entries": []},
    )
    rollback_ledger = _load_json(
        ROLLBACK_LEDGER_PATH,
        {"schema_version": "SelfBuildRollbackLedger.v1", "entry_count": 0, "entries": []},
    )

    rollback_by_mutation: dict[str, list[dict[str, Any]]] = {}
    for row in rollback_ledger.get("entries", []):
        if not isinstance(row, dict):
            continue
        mutation_id = row.get("mutation_id")
        if not isinstance(mutation_id, str) or not mutation_id:
            continue
        rollback_by_mutation.setdefault(mutation_id, []).append(row)

    mutation_scores: list[dict[str, Any]] = []
    for row in mutation_ledger.get("entries", []):
        if not isinstance(row, dict):
            continue
        mutation_id = str(row.get("mutation_id", "UNKNOWN_MUTATION"))
        post_validation = row.get("post_validation", {})
        if not isinstance(post_validation, dict):
            post_validation = {}

        validation_score = _validation_score(post_validation)
        rollbacks = rollback_by_mutation.get(mutation_id, [])
        rolled_back = any(r.get("status") == "ROLLED_BACK" for r in rollbacks)
        rollback_failure = any(r.get("status") == "NOT_COMPUTABLE" for r in rollbacks)

        stability_score = -1 if rolled_back else 1
        integrity_score = 1
        if row.get("before_hash") == "NOT_FOUND" or row.get("after_hash") == "NOT_FOUND":
            integrity_score -= 1
        if rollback_failure:
            integrity_score -= 1

        total_score = validation_score + stability_score + integrity_score
        classification = "REVERTED" if rolled_back else "RETAINED"

        mutation_scores.append(
            {
                "mutation_id": mutation_id,
                "target_path": row.get("target_path", ""),
                "validation_score": validation_score,
                "stability_score": stability_score,
                "integrity_score": integrity_score,
                "total_score": total_score,
                "classification": classification,
                "rollback_count": len(rollbacks),
            }
        )

    rollback_scores: list[dict[str, Any]] = []
    for row in rollback_ledger.get("entries", []):
        if not isinstance(row, dict):
            continue
        mutation_id = str(row.get("mutation_id", ""))
        post_validation = row.get("post_validation", {})
        if not isinstance(post_validation, dict):
            post_validation = {}
        validation_score = _validation_score(post_validation)
        stability_score = 1 if row.get("status") == "ROLLED_BACK" else -1
        integrity_score = 1 if row.get("failure_reason") in (None, "") else 0
        rollback_scores.append(
            {
                "rollback_id": row.get("rollback_id", ""),
                "mutation_id": mutation_id,
                "status": row.get("status", "NOT_COMPUTABLE"),
                "validation_score": validation_score,
                "stability_score": stability_score,
                "integrity_score": integrity_score,
                "total_score": validation_score + stability_score + integrity_score,
            }
        )

    sorted_mutations = sorted(mutation_scores, key=lambda x: (x["total_score"], str(x["mutation_id"])), reverse=True)
    top_mutations = sorted_mutations[:5]
    flagged_mutations = sorted(
        [row for row in mutation_scores if row["total_score"] <= 1 or row["classification"] == "REVERTED"],
        key=lambda x: (x["total_score"], str(x["mutation_id"])),
    )

    payload = {
        "schema_version": "SelfBuildScoring.v1",
        "mutation_scores": mutation_scores,
        "rollback_scores": rollback_scores,
        "top_mutations": top_mutations,
        "flagged_mutations": flagged_mutations,
        "authority": {
            "mutation": False,
            "analysis_only": True,
        },
    }
    payload["canonical_hash"] = _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return payload
