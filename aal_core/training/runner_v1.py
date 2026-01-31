from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
import hashlib
import json
import random
import time

LEDGER_DEFAULT = Path.home() / ".aal" / "ledger" / "training_sessions.jsonl"


def _sha256(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _ensure_ledger_path(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")


@dataclass(frozen=True)
class TrainingResult:
    session_id: str
    pack_id: str
    items_seen: int
    score: float
    findings: Dict[str, Any]
    provenance: Dict[str, Any]


def run_training_session(
    training_ir: Dict[str, Any],
    pack_loader_fn,
    evaluator_fn,
    ledger_path: Optional[Path] = None,
) -> TrainingResult:
    """
    pack_loader_fn(pack_id) -> {"vectors": [vector_dict,...], "corpus": {...}}
    evaluator_fn(vectors_subset, training_ir) -> {score, findings}
    """
    ledger_path = ledger_path or LEDGER_DEFAULT
    _ensure_ledger_path(ledger_path)

    seed = int(training_ir.get("options", {}).get("seed", 0))
    rng = random.Random(seed)

    pack_id = training_ir["pack_id"]
    session_id = training_ir["session_id"]

    pack = pack_loader_fn(pack_id)
    vectors = pack.get("vectors", [])
    requested = set(training_ir.get("vectors", []))

    usable = [v for v in vectors if (not requested) or (v.get("vector_id") in requested)]
    max_items = int(training_ir.get("options", {}).get("max_items", min(10, len(usable))))
    subset = usable[:]
    rng.shuffle(subset)
    subset = subset[:max_items]

    evaluation = evaluator_fn(subset, training_ir)
    score = float(evaluation.get("score", 0.0))
    findings = evaluation.get("findings", {})

    record = {
        "schema_version": "aal.training.ledger_record.v1",
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "session_id": session_id,
        "pack_id": pack_id,
        "training_ir": training_ir,
        "training_ir_hash": _sha256(training_ir),
        "items_seen": len(subset),
        "score": score,
        "findings": findings,
        "findings_hash": _sha256(findings),
        "provenance": {
            "deterministic": True,
            "seed": seed,
            "runner": "aal_core.training.runner_v1",
            "inputs_hash": _sha256({
                "pack_id": pack_id,
                "vector_ids": [v.get("vector_id") for v in subset],
            }),
        },
    }

    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")

    return TrainingResult(
        session_id=session_id,
        pack_id=pack_id,
        items_seen=len(subset),
        score=score,
        findings=findings,
        provenance=record["provenance"],
    )
