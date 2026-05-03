from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json

from .self_build_proposal import run_self_build_proposal
from .self_build_scoring import run_self_build_scoring


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _load_artifact(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    return loaded if isinstance(loaded, dict) else None


def run_self_build_score_feedback() -> dict[str, Any]:
    scoring_artifact = _load_artifact(Path("out/registry/self_build_scoring.latest.json"))
    if scoring_artifact is None:
        scoring_artifact = run_self_build_scoring()

    proposal = run_self_build_proposal()

    if scoring_artifact.get("schema_version") != "SelfBuildScoring.v1" or proposal.get("schema_version") != "SelfBuildProposal.v1":
        payload = {
            "schema_version": "SelfBuildScoreFeedback.v1",
            "status": "NOT_COMPUTABLE",
            "reason": "INVALID_INPUT_ARTIFACT",
            "ranked_targets": [],
            "flagged_targets": [],
            "blocked_targets": [],
            "authority": {"mutation": False, "promotion": False, "execution": False, "analysis_only": True},
        }
        payload["canonical_hash"] = _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        return payload

    score_by_target: dict[str, dict[str, Any]] = {}
    for row in scoring_artifact.get("mutation_scores", []):
        if not isinstance(row, dict):
            continue
        target = row.get("target_path")
        if not isinstance(target, str):
            continue
        previous = score_by_target.get(target)
        if previous is None or row.get("total_score", -999) > previous.get("total_score", -999):
            score_by_target[target] = row

    ranked_targets: list[dict[str, Any]] = []
    flagged_targets: list[dict[str, Any]] = []
    blocked_targets: list[dict[str, Any]] = []

    for item in proposal.get("proposals", []):
        if not isinstance(item, dict):
            continue
        target_path = item.get("target_path", "")
        score_row = score_by_target.get(target_path)
        if score_row is None:
            priority = "MEDIUM"
            total_score = 0
            annotation = "NO_PRIOR_SCORE"
        else:
            total_score = int(score_row.get("total_score", 0))
            if total_score >= 4:
                priority = "HIGH"
                annotation = "HIGH_CONFIDENCE"
            elif total_score >= 2:
                priority = "MEDIUM"
                annotation = "MIXED_SIGNAL"
            else:
                priority = "LOW"
                annotation = "LOW_CONFIDENCE"

        row = {
            "target_path": target_path,
            "priority": priority,
            "score": total_score,
            "annotation": annotation,
            "strategy": item.get("strategy", "IMPLEMENT_MINIMAL_LOGIC"),
        }
        ranked_targets.append(row)

        if priority == "LOW":
            flagged_targets.append({"target_path": target_path, "score": total_score, "reason": annotation})
        if annotation == "LOW_CONFIDENCE":
            blocked_targets.append({"target_path": target_path, "score": total_score, "reason": "REQUIRES_OPERATOR_REVIEW"})

    ranked_targets = sorted(ranked_targets, key=lambda r: (-r["score"], r["target_path"]))
    flagged_targets = sorted(flagged_targets, key=lambda r: (r["score"], r["target_path"]))
    blocked_targets = sorted(blocked_targets, key=lambda r: (r["score"], r["target_path"]))

    payload = {
        "schema_version": "SelfBuildScoreFeedback.v1",
        "status": "OK",
        "proposal_count": proposal.get("proposal_count", 0),
        "ranked_targets": ranked_targets,
        "flagged_targets": flagged_targets,
        "blocked_targets": blocked_targets,
        "source_hashes": {
            "proposal_hash": proposal.get("canonical_hash"),
            "scoring_hash": scoring_artifact.get("canonical_hash"),
        },
        "authority": {"mutation": False, "promotion": False, "execution": False, "analysis_only": True},
    }
    payload["canonical_hash"] = _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return payload
